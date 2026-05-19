/******************************************************************************
 * DESCRIPTION:
 * CTA is an EPICS aSub-based state machine controlling deterministic event
 * sequence playback on the EVG.
 *
 * States:
 *   IDLE    : waits for valid Pulse ID synchronisation 
 *   ARMED   : synchronised, waiting for START command
 *   STARTED : evaluates start conditions (immediate or modulo/offset)
 *   RUNNING : sequence playback in progress
 *   STOPPED : resets CTA state and outputs
 *
 * /!\ Known issue:
 * There is a phase shift between CTA and the visible Pulse ID.
 *
 * +1 : the current Pulse ID corresponds to the previous pulse
 *      (event comes first, Pulse ID RX update comes afterwards).
 *
 * +2 : CTA aSub processes before the Pulse ID RX record is updated
 *      by the mrfioc2_regDev software chain.
 *
 * +3 : STARTED logic must anticipate the pulse on which the first CTA
 *      event will actually be emitted (decision is taken one cycle earlier).
 *
 * This phase relationship is implementation/runtime dependent.
 *
 * TODO:
 * Implement a proper phase alignment detection mechanism instead of relying
 * on hardcoded offsets.
 ******************************************************************************/

#include <aSubRecord.h>
#include <dbDefs.h>
#include <stdlib.h>
#include <dbAccess.h>

typedef enum {
	IDLE=0,
	ARMED,
	RUNNING,
	STARTED,
	STOPPED
} state_t;

static unsigned short     cycles_cnt = 0; // Counter for CTA cycles
static unsigned long long last_pid   = 0; // Last Pulse ID
static unsigned long long saved_pid  = 0; // Saved Pulse ID for sequence offset calculation
static unsigned long long next_pid   = 0; // Next Pulse ID 
static state_t            state      = 0; // State machine current state
static state_t            last_state = 0; // State machine last state

long cta_state_machine(aSubRecord* prec) {

	// Inputs
	epicsUInt16 start          = *(epicsUInt16*) prec->a;
	epicsUInt16 stop           = *(epicsUInt16*) prec->b;
	epicsUInt32 index          = *(epicsUInt32*) prec->c;
	epicsUInt32 running    	   = *(epicsUInt32*) prec->d;
	epicsUInt64 pid            = *(epicsUInt64*) prec->e;
	epicsUInt64 started_at     = *(epicsUInt64*) prec->f;
	epicsUInt32 length         = *(epicsUInt32*) prec->g;
	epicsUInt32 cycles         = *(epicsUInt32*) prec->h;
	epicsUInt32 cfgMod         = *(epicsUInt32*) prec->i;
	epicsUInt32 cfgModDiv      = *(epicsUInt32*) prec->j;
	epicsUInt32 cfgModOff      = *(epicsUInt32*) prec->k;
	epicsUInt16 loadSeqPending = *(epicsUInt16*) prec->l;
      
	// Outputs
	epicsUInt16 *out_start;
	epicsUInt16 *out_stop;
	epicsUInt32 *out_index;
	epicsUInt32 *out_index_global;
	epicsUInt32 *out_running;
	epicsUInt64 *out_started_at;
	epicsUInt16 *out_load_seq;
	epicsUInt16 *out_load_seq_pending;
	epicsUInt16 *out_enable_evt;
	out_start            = (epicsUInt16*) prec->vala;
	out_stop             = (epicsUInt16*) prec->valb;
	out_index            = (epicsUInt32*) prec->valc;
	out_index_global     = (epicsUInt32*) prec->vald;
	out_running          = (epicsUInt32*) prec->vale;
	out_started_at       = (epicsUInt64*) prec->valf;
	out_load_seq         = (epicsUInt16*) prec->valg;
	out_load_seq_pending = (epicsUInt16*) prec->valh;
	out_enable_evt       = (epicsUInt16*) prec->vali;

	// Initialize ALL outputs
	*out_start            = start;
	*out_stop             = stop;
	*out_index            = index;
	*out_index_global     = index;
	*out_running          = running;
	*out_started_at       = started_at;
	*out_load_seq         = 0;
	*out_load_seq_pending = loadSeqPending;
	*out_enable_evt       = 0;

	if(length == 0)
		return 0;

	// State update
	if(stop)                                               state = STOPPED;
	else if(start && (state == ARMED || state == STARTED)) state = STARTED;
	else if(running)                                       state = RUNNING;
	else if(state != ARMED)                                state = IDLE;

	// State machine 
	switch(state) {

		case STOPPED: 
			*out_enable_evt   = 0;             // disable events
			*out_running      = 0;             // update status 'running'
			*out_index        = 0;             // reset index
			*out_index_global = 0;             // reset index
			*out_stop         = 0;             // reset stop button
			cycles_cnt        = 0;             // reset CTA sequenc cycle counter
			saved_pid         = 0;             // reset saved pid
			break;

		case RUNNING:
			++index;
			*out_index        = index;
			*out_index_global = index;
			// CTA sequence end
			if(index >= length) {
				// Manages cycles
				// 0 = forever | >0 = nb cycles
				++cycles_cnt;
				if(cycles && cycles_cnt >= cycles) {
					state           = STOPPED;
					*out_stop       = 1;
					*out_running    = 0;
					*out_enable_evt = 0;
				}
				else {
					*out_index = 0;
					*out_enable_evt = 1;
				}
			}
			else 
				*out_enable_evt = 1;
			if(last_state == STARTED) 
				*out_started_at = pid + 2;     // update starting pid 
			break;

		case STARTED:
			// Manages configuration mode 
			//
			// Uses next PID because aSub processes after events sequence
			next_pid = pid + 3;
			//
			// MODE: 0 = start immediately | 1 = start with divisor and offset
			// Divisor
			if(cfgMod && !saved_pid && (next_pid % cfgModDiv)==0 ) 
				saved_pid = next_pid;
			// Offset 
			if(!cfgMod || (next_pid - saved_pid == cfgModOff)) {
				*out_enable_evt = 1;       // enable events
				*out_running    = 1;       // update status 'running'
				*out_start      = 0;       // reset start button
			}
			break;

		case ARMED:

		case IDLE:
			// Load sequence
			if(loadSeqPending){
				*out_load_seq         = 1; // load sequence flag
				*out_load_seq_pending = 0; // reset load seq pending flag
			}
			// Pulse ID synchronisation 
			// makes sure the pulse ID as changed because jitter can prevent that 
			if(pid == last_pid + 1)
				state = ARMED;
			else 
				state = IDLE;
			last_pid = pid;
			break;

		default:
			break;
	}
	last_state = state;
	return 0;
}

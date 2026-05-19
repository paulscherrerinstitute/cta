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
			// NOTE: there is a shift of 2 pulse ID. One is because the current pulse ID is the previous one
			// (first event, then pulse ID). The second shift is because aSub processes faster than the Pulse ID RX
			// record (from mrfioc2_regDev). A phase detection mechanism would help assert that. For now, we live 
			// with this phase alignement, which is true for all system (but can change as it depends on runtime).
			break;

		case STARTED:
			// Manages configuration mode 
			//
			// Uses next PID because aSub processes after events sequence
			// see NOTE above
			next_pid = pid + 2;
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

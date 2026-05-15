#include <aSubRecord.h>
#include <dbDefs.h>
#include <stdlib.h>
#include <errlog.h>
#include <dbAccess.h>

/* Define states */
typedef enum {
	IDLE=0,
	ARMED,
	RUNNING,
	STARTED,
	STOPPED
} state_t;

static unsigned long long last_pid = 0;
static state_t  state = 0;

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
	epicsUInt32 *out_running;
	epicsUInt64 *out_started_at;
	epicsUInt16 *out_load_seq;
	epicsUInt16 *out_load_seq_pending;
	epicsUInt16 *out_enable_evt;
	out_start            = (epicsUInt16*) prec->vala;
	out_stop             = (epicsUInt16*) prec->valb;
	out_index            = (epicsUInt32*) prec->valc;
	out_running          = (epicsUInt32*) prec->vald;
	out_started_at       = (epicsUInt64*) prec->vale;
	out_load_seq         = (epicsUInt16*) prec->valf;
	out_load_seq_pending = (epicsUInt16*) prec->valg;
	out_enable_evt       = (epicsUInt16*) prec->valh;

	// Initialize ALL outputs
	*out_start            = start;
	*out_stop             = stop;
	*out_index            = index;
	*out_running          = running;
	*out_started_at       = started_at;
	*out_load_seq         = 0;
	*out_load_seq_pending = loadSeqPending;
	*out_enable_evt       = 0;

	if(length == 0)
		return 0;

	// State update
	if(stop)                         state = STOPPED;
	else if(start && state == ARMED) state = STARTED;
	else if(running)                 state = RUNNING;
	else if(state != ARMED)          state = IDLE;

	// State machine 
	switch(state) {
		case STOPPED: 
			*out_enable_evt=0;                 // disable events
			*out_running=0;                    // update status 'running'
			*out_index=0;                      // reset index
			*out_stop=0;                       // reset stop button
			break;
		case RUNNING:
			++index;
        		*out_index = index;
    			if(index >= length) {
				state=STOPPED;
        			*out_stop       = 1;
        			*out_running    = 0;
        			*out_enable_evt = 0;
    			}
    			else {
        			*out_enable_evt = 1;
    			}

    			break;
		case STARTED:
			*out_enable_evt = 1;               // enable events
			*out_running    = 1;               // update status 'running'
			*out_start      = 0;               // reset start button
			*out_started_at = pid;             // update starting pid
			break;
		case ARMED:
		case IDLE:
			/* Sequence update */
			if(loadSeqPending){
				*out_load_seq         = 1; // load sequence flag
				*out_load_seq_pending = 0; // reset load seq pending flag
			}
			/* Pulse ID synchronisation */
			if(pid == last_pid+1)
				state = ARMED;
			else 
				state = IDLE;
			last_pid = pid;
			break;
		default:
			break;
	}
	return 0;
}

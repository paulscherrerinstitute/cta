#include <aSubRecord.h>
#include <dbDefs.h>
#include <stdlib.h>
#include <errlog.h>
#include <dbAccess.h>

/* Define states */
typedef enum {
	IDLE=0,
	RUNNING,
	STARTED,
	STOPPED
} state_t;

/* static variables */
static unsigned long long last_pid      = 0;
 
long cta_state_machine(aSubRecord* prec) {

	unsigned short next_index=0;
	state_t state;

	// Inputs
	unsigned short start          = *(unsigned short*)     prec->a;
	unsigned short stop           = *(unsigned short*)     prec->b;
	unsigned short index          = *(unsigned short*)     prec->c;
	unsigned short running        = *(unsigned short*)     prec->d;
	unsigned long long pid        = *(unsigned long long*) prec->e;
	unsigned long long started_at = *(unsigned long long*) prec->f;
	unsigned short missed_pid     = *(unsigned short*)     prec->g;
	unsigned short length         = *(unsigned short*)     prec->h;
	unsigned short cycles         = *(unsigned short*)     prec->i;
	unsigned short cfgMod         = *(unsigned short*)     prec->j;
	unsigned short cfgModDiv      = *(unsigned short*)     prec->k;
	unsigned short cfgModOff      = *(unsigned short*)     prec->l;
      
        // Outputs
	unsigned short     *out_start;
	unsigned short     *out_stop;
	unsigned short     *out_index;
	unsigned short     *out_running;
	unsigned long long *out_started_at;
	unsigned short     *out_missed_pid;
	unsigned short     *out_load_seq;
	unsigned short     *out_enable_evt;
	out_start      = (unsigned short*)     prec->vala;
	out_stop       = (unsigned short*)     prec->valb;
	out_index      = (unsigned short*)     prec->valc;
	out_running    = (unsigned short*)     prec->vald;
	out_started_at = (unsigned long long*) prec->vale;
	out_missed_pid = (unsigned short*)     prec->valf;
	out_load_seq   = (unsigned short*)     prec->valg;
	out_enable_evt = (unsigned short*)     prec->valh;

	// Initialize ALL outputs
	*out_start       = start;
	*out_stop        = stop;
	*out_index       = index;
	*out_running     = running;
	*out_started_at  = started_at;
	*out_missed_pid  = missed_pid;
	*out_load_seq    = 0;
	*out_enable_evt  = 0;

	if(length == 0)
		return 0;

	// State update
	if(stop)         state = STOPPED;
	else if(start)   state = STARTED;
	else if(running) state = RUNNING;
	else             state = IDLE; 

	// State machine 
	switch(state) {
		case STOPPED: 
			*out_enable_evt=0;  		// disable events
			*out_running=0;     		// update status 'running'
			*out_index=0;      		// reset index
			*out_stop=0;        		// reset stop button
			break;
		case STARTED:
			*out_enable_evt=1;  		// enable events
			*out_running=1;     		// update status 'running'
			*out_load_seq=1;    		// load sequence flag
			*out_start=0;       		// reset start button
			*out_started_at=pid;            // update starting pid
			break;
		case RUNNING:
			next_index = index + 1;
    			*out_load_seq = 0;

    			// stop BEFORE invalid index
    			if(next_index >= length) {
				state=STOPPED;
        			*out_stop       = 1;
        			*out_running    = 0;
        			*out_enable_evt = 0;

        			// keep last VALID index
        			if(length > 0)
            				*out_index = length - 1;
        			else
            				*out_index = 0;
    			}
    			else {
			
        			*out_index      = next_index;
        			*out_enable_evt = 1;
    			}

    			if(last_pid == pid)
        			*out_missed_pid = missed_pid + 1;

    			break;
		case IDLE:
		default:
			break;
	}
	last_pid=pid;
	return 0;
}

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

/* State variable */
static state_t state = IDLE;

int i=0;
 
long cta_state_machine(aSubRecord* prec) {

	// Inputs
	unsigned short start      = *(unsigned short*)     prec->a;
	unsigned short stop       = *(unsigned short*)     prec->b;
	unsigned short length     = *(unsigned short*)     prec->c;
	unsigned short cycles     = *(unsigned short*)     prec->d;
	unsigned short cfgMod     = *(unsigned short*)     prec->e;
	unsigned short cfgModDiv  = *(unsigned short*)     prec->f;
	unsigned short cfgModOff  = *(unsigned short*)     prec->g;
	unsigned long long cfgPid = *(unsigned long long*) prec->h;
	unsigned short index      = *(unsigned short*)     prec->i;
	unsigned short running    = *(unsigned short*)     prec->j;
	unsigned short started_at = *(unsigned short*)     prec->k;
	unsigned short missed_pid = *(unsigned short*)     prec->l;
      
        // Outputs
	unsigned short *out_start;
	unsigned short *out_stop;
	unsigned short *out_index;
	unsigned short *out_running;
	unsigned short *out_started_at;
	unsigned short *out_missed_pid;
	unsigned short *out_enable_seq;
	out_start      = (unsigned short*) prec->vala;
	out_stop       = (unsigned short*) prec->valb;
	out_index      = (unsigned short*) prec->valc;
	out_running    = (unsigned short*) prec->vald;
	out_started_at = (unsigned short*) prec->vale;
	out_missed_pid = (unsigned short*) prec->valf;
	out_enable_seq = (unsigned short*) prec->valg;

	// State update
	if(stop)         state = STOPPED;
	else if(start)   state = STARTED;
	else if(running) state = RUNNING;
	else             state = IDLE; 

	switch(state) {

		case STOPPED: 
			*out_running=0;     // update status 'running'
			*out_index=0;       // reset index
			*out_stop=0;        // reset stop button
			break;
		case STARTED:
			*out_running=1;     // update status 'running'
			*out_start=0;       // reset start button
			break;
		case RUNNING:
			*out_running=1;	    // update status 'running'	
			if(index < length)
				*out_index=++index; 
			else 
				*out_stop=1;
			*out_enable_seq=1;
			errlogPrintf("OUT ENAB SEQ : %d\n",*out_enable_seq);
			break;

	}

	if(i%100==0) {
		errlogPrintf(
				"start:%d, stop:%d, len:%d, cycles:%d, cfgMod:%d, cfgModDiv:%d, cfgModOff:%d, out_enable_seq=%d, cfgPid:%llu\n",
				start,stop,length,cycles,cfgMod,cfgModDiv,cfgModOff,*out_enable_seq,cfgPid
				);
	}
	i++;
	

	return 0;
}

#include <aSubRecord.h>
#include <dbDefs.h>
#include <stdlib.h>
#include <errlog.h>

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
      
        // Outputs
	unsigned short *out_index;
	unsigned short *out_running;
	unsigned short *out_enabled;
	unsigned short *out_load;
	unsigned short *out_started_at;
	unsigned short *out_missed_pid;
	out_index      = (unsigned short*) prec->vala;
	out_running    = (unsigned short*) prec->valb;
	out_enabled    = (unsigned short*) prec->valc;
	out_load       = (unsigned short*) prec->vald;
	out_started_at = (unsigned short*) prec->vale;
	out_missed_pid = (unsigned short*) prec->valf;
	
	if(i%100==0) {
		errlogPrintf(
				"start:%d, stop:%d, len:%d, cycles:%d, cfgMod:%d, cfgModDiv:%d, cfgModOff:%d, cfgPid:%llu\n",
				start,stop,length,cycles,cfgMod,cfgModDiv,cfgModOff,cfgPid
				);
	}

	i++;
	return 0;
}

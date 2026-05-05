/*
 * main_proj.cpp
 *
 *  Created on: 03 Jan. 2017
 *      Author: Mironov
 */
#include "track_util.h"
#include "parsePrm.h"


void binning(const char *fname){
	bTrack *tmp=new bTrack();

	tmp->writeBinnedProf(fname);
	del(tmp);
	if(fProfile) del(fProfile);
}


int main(int argc, char **argv) {
// {debugFg=DEBUG_LOG|DEBUG_PRINT; clearDeb(); }
 prog_flag=BN;
 progDescription="\nThe Binning program create a track with binned data\n\
 Usage:\n\
 $ ./binning [-parameters] track1 track2 ...";
 _version=version;
 	initSG(argc, argv);
	for(int i=0; i<nfiles; i++){
		char *fname=files[i].fname;
		if(fname==0 || strlen(trim(fname))==0) continue;
		binning(fname);
	}


	fflush(stdout);
	fclose(stdout);
	return 0;
}









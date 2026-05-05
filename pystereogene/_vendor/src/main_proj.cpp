/*
 * main_proj.cpp
 *
 *  Created on: 03 Jan 2017
 *      Author: andrey
 */
#include "track_util.h"
#include "parsePrm.h"


int main(int argc, char **argv) {
//	clearDeb(); debugFg=DEBUG_LOG|DEBUG_PRINT;
	prog_flag=PRJ;
	confFile=strdup("confounder.bgraph");
	progDescription="\
The Projection program creates tracks with exclusion of the defined confounder\n\
Usage:\n\
$ ./Projection [-parameters] track1 track2 ...";
	_version=version;

	initSG(argc, argv);

	Preparator();

	Projector();
	fflush(stdout);
	fclose(stdout);
	return 0;
}









#include "track_util.h"
#include "parsePrm.h"
#include <dirent.h>
#include <sys/types.h>
#include <sys/stat.h>

//==============================================================================
// for debugging :
// set debugFg=DEBUG_LOG|DEBUG_PRINT
// set debS string for module identification//
// Use:  deb(n);  // print debug information as number
//       deb(format,...)    // print debug information as printf
//       deb(n,format,...)  // print debug information as a number and printf
// example:
// debS="fun1";
// deb(1);
// ....
// deb(2,"%i %f", n, d);
// ....
// deb("OK");


//=========================================================================
//=========================================================================
//=========================================================================
//=========================================================================
//=========================================================================
//=========================================================================

int main(int argc, char **argv) {
//	test("../Tracks/RCDB_all_to_all");
//	debugFg=DEBUG_LOG|DEBUG_PRINT; clearDeb();
	progDescription="The StereoGene program compares pairs of tracks and calculates kernel correlations\n\
Usage:\n\
$ ./StereoGene [-parameters] trackFile_1 trackFile_2 ... trackFile_n";
	_version=version;
	prog_flag=SG;
	initSG(argc, argv);
	writeLog("====== Start ====== deb=%i\n",debugFg);

//===========================================
	Preparator();
	Correlator();
	fflush(stdout);
	writeLog("====== End ======\n");
	return 0;
}

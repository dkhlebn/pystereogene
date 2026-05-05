#include "track_util.h"
#include "parsePrm.h"


//=========================================
//=========================================
//=========================================
//==========================================================================================



void testMtx(){
	int n=3;
	double mm[]={	1,   -0.2,	0.3,
				 -0.2,    1,	0.1,
				  0.3,	0.1,	1
	};
	VectorX *v=new VectorX(n);
	Matrix *m=new Matrix(n,mm);
	m->printMtx();

	m->eigen(v);
	v->print();

	exit(0);
}


int main(int argc, char **argv) {
//	debugFg=3;
	prog_flag=CNF;
//	testMtx();
	progDescription="The Confounder program creates a confounder track using set of the tracks\n\
Usage:\n\
$ ./Confounder [-parameters] <list file>\n";
	_version=version;
	initSG(argc, argv);

	Preparator();
	Covariator();
	fflush(stdout);
	fclose(stdout);
	return 0;
}

/*
 * parsePrm.cpp
 *
 *  Created on: Feb 2, 2017
 *      Author: Mironov
 */
#include "util.h"
#include "parsePrm.h"
#include <unistd.h>

#if defined(_WIN32)
#include <conio.h>
int nHelpLines=30;
#else
#include <termios.h>
int nHelpLines=2000;
#endif

int xpause(){
	int c=0;
#if defined(_WIN32)
	c=_getch(); printf("\n%c\n",c);
#else
//	return 0;
	struct termios oldt, newt;
	tcgetattr( STDIN_FILENO, &oldt);
	newt = oldt;
	newt.c_lflag &= ~(ICANON);
	tcsetattr( STDIN_FILENO, TCSANOW, &newt);
	c=getchar();
	tcsetattr( STDIN_FILENO, TCSANOW, &oldt);
#endif
	return c;
}


const int PRM_INT=1;
const int PRM_DOUBLE=2;
const int PRM_STRING=3;
const int PRM_ENUM=4;
const int PRM_FG=5;
const int PRM_PATH=7;

const int PRM_UNKNOWN=-0XFFFFFFF;
int prog_flag=1;

//===================== convert text flag to a binary
int getFlag(char*s){
	int fg=0;
	if(		keyCmp(s,"1")==0 || keyCmp(s,"YES")==0 || keyCmp(s,"ON" )==0) {fg=1;}
	else if(keyCmp(s,"0")==0 || keyCmp(s,"NO")==0  || keyCmp(s,"OFF")==0) {fg=0;}
	else fg=-1;
	return fg;
}
//===================================================================

NamedRes::NamedRes(const char *nm, double *v){name=nm; value=v; type=PRM_DOUBLE; f=0;}
NamedRes::NamedRes(const char *nm, int *v){name=nm; value=v; type=PRM_INT; f=0;}
NamedRes::NamedRes(const char *nm, char **v){name=nm; value=(void*) v; type=PRM_STRING; f=0;}
NamedRes::NamedRes(const char *nm, char* (*ff)()){name=nm; value=0; type=PRM_STRING; f=ff;}
NamedRes::NamedRes(const char *nm){name=nm; value=0; type=0; f=0;}

char* NamedRes::printValue(char *buf, int siz){
	if(type==0) return strcpy(buf,name);
	if(f) return f();
	switch(type){
	case PRM_STRING:{
		char *s=*((char**)value);
		if(s) snprintf(buf,siz,"%s",s);
		else  snprintf(buf,siz,"NA");
		break;}
	case PRM_DOUBLE:
		{double *d=(double *)value;
		if(*d==FNA)              snprintf(buf,siz,"NA");
		else if(abs(*d) > 0.1)   snprintf(buf,siz,"%.3f",*d);
		else if(abs(*d) > 0.01)  snprintf(buf,siz,"%.4f",*d);
		else if(abs(*d) > 0.001) snprintf(buf,siz,"%.5f",*d);
		else 					 snprintf(buf,siz,"%.2e",*d);
		break;}
	case PRM_INT:
		{int *k=(int *)value;
		if(*k==NA) 				snprintf(buf,siz,"NA");
		else 					snprintf(buf,siz,"%i",*k);
		break;}
	}
	return buf;
};

int NamedRes::printValue(FILE *out){
	if(type==0) return fprintf(out,"%s",name);
	if(f) return fprintf(out, "%s", f());
	switch(type){
	case PRM_STRING:{
		char *s=*((char**)value);
		if(s) return fprintf(out,"%s",s);
		else  return fprintf(out,"NA");
		break;}
	case PRM_DOUBLE:
		{double *d=(double *)value;
		if(*d==FNA) return fprintf(out,"NA");
		else if(abs(*d) > 0.1  ) return fprintf(out,"%.3f",*d);
		else if(abs(*d) > 0.01 ) return fprintf(out,"%.4f",*d);
		else if(abs(*d) > 0.001) return fprintf(out,"%.5f",*d);
		else return fprintf(out,"%.2e",*d);
		break;}
	case PRM_INT:
		{int *k=(int *)value;
		if(*k==NA) return fprintf(out,"NA");
		else return fprintf(out,"%i",*k);
		break;}
	}
	return 0;
};

//===================================================================================================
Param *findParam(const char * name);
void readPrm(char *s);
void readPrm(char *key, char *val);
void printHelp();

//===================================================================================================
//Param *pparams[]={
//================================================== Common parameters
//		new Param(AP,"common parameters"),
//		new Param(AP,"v"		    ,0, &verbose	,1, "verbose"),
//		new Param(AP,"syntax"		,0, &syntax		,1, "strong syntax control in input files"),
//		new Param(AP,"verbose"		,0, &verbose	,   "verbose"),
//		new Param(AP,"s"		    ,0, &silent		,1, "no output to stdout"),
//		new Param(AP,"silent"		,0, &silent		,	"no output to stdout"),
////======================== =====================================================================================
//		new Param(AP,"preparation parameters"),
//		new Param(AP,"bin" 	 		,1, &binSize  		,"bin size for input averaging"),
//		new Param(AP,"clear" 		,0, &clearProfile 	,"force binary profile preparation"),
//		new Param(AP,"c" 	  		,0, &clearProfile 	, 1,"force  binary profile preparation"),
//		new Param(SM,"smoothZ" 		,0, &smoothZ 		, "Z-Score for smoothed profile"),
////======================== =====================================================================================
//		new Param(AP,"paths and files"),
//		new Param(AP,"cfg" 			,0, &cfgFile 		,"config file"),
//		new Param(AP,"profPath" 	,1, &profPath 		,"path for binary profiles", true),
//		new Param(AP,"trackPath" 	,1, &trackPath 		,"path for tracks", true),
//		new Param(BN,"binPath" 		,1, &binPath 		,"path for bined tracks", true),
//		new Param(SM,"smoothPath"	,1, &smoothPath 	,"path for smoothed tracks", true),
//		new Param(SG,"resPath" 		,1, &resPath 		,"path for results", true),
//		new Param(SG,"report" 		,1, &reportPath		,"path for reports. relative to the resPath", true),
//
//		new Param(AP,"confounder"	,0, &confFile		,"confounder filename"),
//		new Param(AP,"aliases"		,0, &aliasFile		,"Aliase table"),
//
//		new Param(SG,"statistics"	,0, &statFileName	,"cumulative file with statistics"),
//		new Param(SG,"params" 		,0, &paramsFileName	,"cumulative file with parameters"),
//		new Param(AP,"log" 			,0, &logFileName	,"cumulative log-file"),
////		new Param(AP,"id_suff" 		,0, &idSuff		,0),	// suffix for the result files
////======================== =====================================================================================
//		new Param(AP, "input parameters"),
//		new Param(AP, "chrom"		,1, &chromFile	,"chromosome file"),
//		new Param(AP, "BufSize"		,0, &binBufSize	,"Buffer Size"),
//		new Param(AP, "bpType" 		,1, &bpType  		,bpTypes	,"The value used as a score for BroadPeak input file"),
////		new Param(SG|PRJ,"pcorProfile" ,1, &pcorProfile	,"Track for partial correlation"),
//		new Param(PRJ,"outPrjBGr"   ,0, &outPrjBGr		,"Write BedGraph for projections"),
//		new Param(SG, "NA"       	,1, &NAFlag     	,1 , "use NA values as unknown and fill them by noise"),
//		new Param(SG, "threshold"	,1, &threshold	,"threshold for input data for removing too small values: 0..250"),
////======================== =====================================================================================
//		new Param(SG, "Analysis parameters"),
//		new Param(SG, "kernelType"	,1, &kernelType	,kernelTypes,0),
//		new Param(SG, "customKern"	,1, &customKern	,0),
//		new Param(SG, "kernelSigma"	,3, &kernelSigma,"Kernel width"),
//		new Param(SG, "kernelShift"	,1, &kernelShift,0),
//		new Param(SG, "wSize" 	  	,3, &wSize  	,"Window size"),
//		new Param(SG, "wStep" 	  	,1, &wStep  	,0),
//		new Param(SG, "kernelNS"	,0, &kernelNS  	,0),
//		new Param(SG, "flankSize"	,1, &flankSize  ,0),
//		new Param(SG, "maxNA"		,1, &maxNA0  	,"Max number of NA values in window (percent)"),
//		new Param(SG, "maxZero"		,1, &maxZero0  	,"Max number of zero values in window (percent)"),
//		new Param(SG, "nShuffle"	,1, &nShuffle  	,"Number of shuffles for background calculation"),
//		new Param(SG, "noiseLevel"	,1, &noiseLevel ,0),
//		new Param(SG, "complFg"		,1, &complFg	,complFlags,0),
//		new Param(SG, "localShuffle" ,1, &localShuffle,1,"Use cyclic permutations"),
////==============================================================================================================
//		new Param(SG, "Output parameters"),
//		new Param(SG, "outSpectr" 	,1, &outSpectr    ,"write fourier spectrums"),
//		new Param(SG, "outChrom" 	,1, &outChrom     ,"write statistics by chromosomes"),
//		new Param(SG, "writeDistr" 	,1, &writeDistr, distrTypes   ,"write foreground and background distributions"),
//		new Param(SG, "plotType" 	,1, &RScriptFg,  PlotTypes    ,0),
//		new Param(SG, "r" 			,0, &RScriptFg    ,R,"write R script for the result presentation"),
//		new Param(SG, "crossWidth" 	,0, &crossWidth   ,0,"Width of cross-correlation plot"),
//		new Param(SG, "Cross" 		,1, &writeDistCorr,1,"Write cross-correlations"),
//		new Param(SG, "outLC"		,1, &outLC	,LCFlags  ,0),
//		new Param(SG, "lc"			,0, &outLC		  ,	LC_BASE,"produce profile correlation"),
//		new Param(SG, "LCScale"		,0, &LCScale	  ,LCScaleTypes,"Local correlation scale: LOG | LIN"),
//		new Param(SG, "L_LC"		,1, &L_LC	      ,"threshold on correlation when write the local correlation"),
//		new Param(SG, "R_LC"		,1, &R_LC	      ,"threshold on correlation when write the local correlation"),
//		new Param(SG, "outRes" 		,0, &outRes 	  ,outResTypes,"format for results in statistics file"),
//		new Param(SG, "AutoCorr"  	,1, &doAutoCorr   ,0),
//		new Param(SG, "aliases"  	,1, &aliasFile    ,0),
//		new Param(SG, "Rscript"   	,1, &Rscript      ,0),
//		new Param(SG, "plotH"   	,1, &plotH    	  ,0),
//		new Param(SG, "plotW"   	,1, &plotW    	  ,0),
//
////======================== =================== Additional parameters (see Undocumented) ===============================
//		new Param(AP, "debug"		,0, &debugFg   	  ,0),	//debug mode
//		new Param(AP, "d"			,0, &debugFg   	  ,1, 0),	//debug mode
//		//===================================== ParseGenes parameters =================
//		new Param(PG, "gencodeLevel",1, &pgLevel  	  ,1, 0),	//max level in ENCODE to be taken into account
//		new Param(PG, "biotypes"	,1, &biotypes	  ,"Biotypes Filter"),	//minimal biotypes filter
//
//		new Param(AP, "Happy correlations!"),
//		0,
//};

//=================================================================================================
//===================================  End declaration ============================================
//=================================================================================================
void Param::init(int prg, const char* _name,int print,void *_prm, int _type, Name_Value **fg, const char* descr){
	name=_name;
	printFg=print;
	enums=fg;
	description=descr;
	prm=_prm;
	type=_type;
	value=PRM_UNKNOWN;
	prog_fg=prg;
}

void Param::init(int fg,const char* _name,int print,void *_prm, int _type, const char* descr){
	name=_name;
	printFg=print;
	description=descr;
	prm=_prm;
	type=_type;
	value=PRM_UNKNOWN;
	prog_fg=fg;
}
Param::Param(int fg,const char* descr)
	{init(fg,0,0,0,0 ,descr);}
Param::Param(int fg,const char* _name,int print,  int    *_prm, const char* descr)
	{init(fg,_name,print,_prm,PRM_INT	,descr);}
Param::Param(int fg,const char* _name,int print,  bool   *_prm,  const char* descr)
	{init(fg,_name,print,_prm,PRM_FG		,descr);}
Param::Param(int fg,const char* _name,int print,  double *_prm,  const char* descr)
	{init(fg,_name,print,_prm,PRM_DOUBLE	,descr);}
Param::Param(int fg,const char* _name,int print,  char*  *_prm, const char* descr)
	{init(fg,_name, print,_prm,PRM_STRING	,descr);}
Param::Param(int fg,const char* _name,int print,  char*  *_prm, const char* descr, bool path)
	{init(fg,_name,print,_prm,PRM_PATH	,descr);}
Param::Param(int fg,const char* _name,int print,  int    *_prm, int val, const char* descr)
	{init(fg,_name,print,_prm,PRM_INT	,descr);	value=val;}
Param::Param(int fg,const char* _name,int print,  bool    *_prm, bool val, const char* descr)
	{init(fg,_name,print,_prm,PRM_FG	,descr);	value=val;}
Param::Param(int prg, const char* _name,int print,  int    *_prm, Name_Value **fg, const char* descr)
	{init(prg,_name,print,_prm,PRM_ENUM	,fg,descr);}
//====================================================================================================

//====================================================================================================
int Param::readEnum(char *s){
	for(int i=0; enums[i]!=0; i++){
		if(keyCmp(enums[i]->name, s) ==0) return enums[i]->value;
	}
	return PRM_UNKNOWN;
}


int Param::readVal(char *s){
	s=trim(s);
	int fg=0;
	switch(type){
	case PRM_INT:  		{
		s=strtok(skipSpace(s),",; \t");
		if(isDouble(s))		//============= number like '1.5k' allowed
			*(int *)  (prm)=readInt(s);
		else
			fg=1;
		break;
	}
	case PRM_FG:		{
		int x=getFlag(s);
		if(x==-1) fg=1;
		else *(bool*)  (prm)=x;
		break;
	}
	case PRM_DOUBLE:   	{
		s=strtok(skipSpace(s),",; \t");
		if(isDouble(s))
			*(double*)(prm)=readDouble(s);
		else fg=1;
		break;
	}
	case PRM_STRING:
		if(s==0 || strlen(s)) *(char**) (prm)=strdup(s);
		else prm=0;
		break;
	case PRM_PATH:
		if(s==0 || strlen(s)) *(char**) (prm)=makePath(s);
		else prm=0;
		break;
	case PRM_ENUM:		{
		int vl=readEnum(s);
		if(vl!=PRM_UNKNOWN) *(int *)(prm)=vl;
		else	fg=1;
		break;
	}

	default: fg=1; break;
	}
	return fg;
}
void Param::setVal(){
	switch(type){
	case PRM_INT:  		*(int *)  (prm)=value; break;
	case PRM_FG:		*(bool*)  (prm)=value; break;
	default: break;
	}
}




//===========================================================================================================
char *Param::printParamValue(char *buf, int siz){
	strcpy(buf,"NONE");
	switch(type){
	case PRM_INT: 		snprintf(buf,siz,"%i",*(int *)prm); break;
	case PRM_DOUBLE: 	snprintf(buf,siz,"%.2g",*(double*)prm); break;
	case PRM_STRING: 	if(prm){
		char *s=*(char**)prm;
		if(s) snprintf(buf,siz,"%s",s);} break;
	case PRM_FG: 		snprintf(buf,siz,"%i",(*(int*)prm) ? 1:0); break;
	case PRM_PATH:		if(prm){
		char *s=*(char**)prm;
		if(s) snprintf(buf,siz,"%s",s);} break;
	}
	return buf;
}
//===========================================================================================================
int Param::printParamValue(FILE *out){
	switch(type){
	case PRM_INT: 		fprintf(out,"%i",*(int *)prm); break;
	case PRM_DOUBLE: 	fprintf(out,"%.2g",*(double*)prm); break;
	case PRM_STRING:
		if(prm){
		char *s=*(char**)prm;
		if(s) fprintf(out,"%s",s);
		else  fprintf(out,"NONE");}
		else  fprintf(out,"NONE");
		break;
	case PRM_FG: 		fprintf(out,"%i",(*(int*)prm) ? 1:0); break;
	case PRM_PATH:		if(prm){
		char *s=*(char**)prm;
		if(s) fprintf(out,"%s",s);} break;
	}
	return 0;
}




char *Param::printParamXML(char *buf, int siz){
	char bb[4096];
	snprintf(buf,siz,"%s=\"%s\"",name,printParamValue(bb,siz));
	return buf;
}


//===========================================================================================================
void Param::printDescr(){
	if(description==0) return;
	if((prog_fg & prog_flag)==0)return;
	if(name ==0 || strlen(name)==0) {printf("\n====================== %s ====================== \n",description); return;}
	printf("-%s ", name);
	if(value==PRM_UNKNOWN) {
		if(type==PRM_INT) 	 printf("<int>");
		if(type==PRM_DOUBLE) printf("<float>");
		if(type==PRM_STRING) printf("<string>");
		if(type==PRM_PATH) printf("<string>");
		if(type==PRM_FG)     printf("<0|1>");
	}
	printf("\t%s\n",description);
}
//============================================ Check if param name exists =============================
Param *findParam(const char * name){
	for(int i=0; pparams[i]!=0; i++){
		if(pparams[i]->name == 0) continue;
		if(keyCmp(pparams[i]->name,name)==0) return pparams[i];
	}
	return 0;
}


//============================================ Read Config =========================================
void readConfig(const char * cfg){
	FILE *f=fopen(cfg,"rt");

	if(f==0) return;
	char b[1024], *s;
	for(;(fgets(b,sizeof(b),f))!=0;){
		strtok(b,"\r\n");
		s=skipSpace(b);
		if(*s=='#') continue;
		if(*s==0) continue;
		s=skipSpace(b);
		if(*s==0) continue;
		readPrm(s);
	}
	fclose(f);
}
//============================================ Read Param =========================================
void readPrm(char *b){
	char *prm=strtok(b,"#");
	char *val=strchr(b,'=');
	if(*val==0)  val=b+strlen(b);
	else 		*val++=0;
	readPrm(trim(prm), trim(val));
}


void readPrm(char *key, char *val){
	if(keyCmp(key,"cfg")==0) readConfig(val);
	Param* prm=findParam(key);
	if(prm!=0){
		if(prm->readVal(val)) errorExit("unknown value %s=%s",key,val);
	}
	else errorExit("unknown parameter {%s}",key);
}


char *inFiles[256];
int nInFiles=0;
//============================================ Parse comand line =========================================
void parseArgs(int argc, char **argv){
	char b[1024];
	//========================= Search for cgf ========================
	for(int i=1; i<argc; i++){
		if(*argv[i]=='-'){
			char *s=argv[i];
			for(;*s=='-';s++);
			strcpy(b,s);
			if(keyCmp("cfg",b)==0) readConfig(argv[++i]);
		}
		if(strchr(argv[i],'=')){
			strcpy(b,argv[i]);
			char *s=strtok(b,"=");
			if(keyCmp("cfg",s)==0){
				readConfig(strtok(0,"= "));
			}
		}
	}
	//============================== Read command params =====================
	for(int i=1; i<argc; i++){
		if(*argv[i]=='-'){
			if(keyCmp("h",argv[i]+1)==0){
				printHelp();
				exit(0);
			}
			Param* prm=findParam(argv[i]+1);
			if(prm==0) errorExit("unknown parameter %s", argv[i]+1);
			if(prm->value!=PRM_UNKNOWN) prm->setVal();
			else if(prm->readVal(argv[++i])) errorExit("unknown value %s=%s",argv[i-1],argv[i]);
		}
		else if(strchr(argv[i],'=')){
			readPrm(argv[i]);
		}
		else{
			inFiles[nInFiles++]=argv[i]; // store filenames from input
		}
	}


	if(verbose) silent=false;
}


//==============================================================================
//================================================== search appropriate cfg file
//void readCfg(int argc, const char *argv[]) {
//	argv[0]=correctFname(argv[0]);
//	char b[1024];
//  getFnameWithoutExt(b,argv[0]);
//	strcat(b,".cfg");
//	char *cfg=cfgName(b, (char*)"cfg");
//	readCfg(cfg);					// deafult cfg
//	char* cfg1=strrchr(cfg,'/');	// cfg in current directory
//	if(cfg1 !=0) readCfg(cfg1+1);
//	for(int i=0; i<argc; i++){
//		if(strncmp(argv[i],"cfg=",4)==0) {
//			verb("read cfg <%s>\n",cfg);
//			readCfg((char*)(argv[i]+4));
//		}
//	}
//}

const char *progDescription=0;
const char *_version=0;

void printProgDescr(){
	const char* sp="========================================================================";
	if(progDescription) printf("%s\n%s\n%s\n",sp,progDescription,sp);
	if(_version)	printf("=== Version %s ===\n",_version);
}

void printHelp(){
	printProgDescr();
	for(int i=0, j=0; pparams[i]!=0; i++){
		pparams[i]->printDescr();
		if(j%nHelpLines==0 && j>0) {
			printf("Press q or Esc to exit or any key to go on");
			fflush(stdout);
			int c=xpause();
			printf("\n");
			if(c=='q' || c=='Q' || c==27) {break;}
		}
		 j++;
	}
}

//==============================================================================
//==============================================================================
//==============================================================================
//==============================================================================
//==============================================================================

















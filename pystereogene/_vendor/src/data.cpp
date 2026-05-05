/*
 * data.cpp
 *
 *      Author: Mironov
 */


#include "track_util.h"
#include "parsePrm.h"


const char* version="2.51";




Chromosome *chrom_list;       // list of chromosomes
Chromosome *curChrom=chrom_list;
int  binSize=100;   // frame size fo profile
bool  NAFlag=0;


long long GenomeLength=0;   // TOTAL LENGTH OF THE GENOME
int n_chrom;
char trackName[4096];       // current track name
char *chromFile=0;
char *confFile=0;		    // confounder file name

char *cfgFile=0;		    // config file name
char *profPath	=strdup("");
char *trackPath	=strdup("");
char *binPath	=strdup("");
char *smoothPath=strdup("");
char *resPath	=strdup("");
char *reportPath=0;	        // path to the report files
const char*defaultConfig="stereogene.cfg";

char curOutPath [1024];	// current output path
char curRepPath [1024];
char curOutFname[1024];	// current output file without ext
char outFile    [TBS];	// common pathname for outputs
char curReport  [TBS];	// fille pathname for reports relative to curOutPath
char reportPDF	[TBS];	// PDF  report
char reportHTML	[TBS];	// HTML report

char *statFileName=(char*)"./statistics";
char *paramsFileName=(char*)"./params";
char *inputProfiles=0;
AliasTable *aliases=0;
char* aliasFile=0;
char* Rscript=(char*)"Rscript";
int  plotH=3;
int  plotW=7;

//char *outTrackFile=0; // Filename for write out track
//char *idSuff=(char*)"";


bool  syntax=1;				// Strong syntax control

int   complFg=IGNORE_STRAND;
int   profileLength;			// size of the profile array

int  binBufSize=100000000;

int 	kernelType=KERN_NORM;
char* 	customKern=0;
double 	noiseLevel=0;
int 	wSize=300000;        	// size of widow (nucleotides)
int 	wStep=0;             	// window step   (nucleotides)
int 	flankSize=0;
int 	kernelSigma=1000.;    	// kernel width (nucleotides)
int 	kernelShift=0;      	// Kernel mean (for Gauss) or Kernel start for exponent
int 	intervFg0;
double 	scaleFactor=0.2;


//==================== Output
int   	writeDistr=DISTR_SHORT;
bool  	writeDistCorr=1;		    // write BroadPeak
int   	crossWidth=10000;
bool  	outSpectr=0;
bool  	outChrom=0;
int   	outRes=TAB;
double 	totCorr=FNA, BgTotal=FNA;
int 	RScriptFg=0;


//===================================== Local correlation track
int 	outLC=0;
int 	LCScale=LIN_SCALE;
double 	L_LC=0;		// Left treshold to write the Local Correlation track
double 	R_LC=0;		// Right treshold on write the Local Correlation track


//=================================================================
bool 	outPrjBGr=true;

int 	wProfStep=0;          	// window step   (profile scale)
int 	wProfSize=0;          	// size of widow (profile scale)
int 	LFlankProfSize=0;         // size of flank (profile scale)
int 	RFlankProfSize=0;         // size of flank (profile scale)
int 	profWithFlanksLength=0; 	// size of profWindow array (including random flanks)
bool	localShuffle=0;			// use shuffle inside the windoww
double 	kernelProfSigma=1000;     // kernel width ((profile scale)
double 	kernelProfShift=0;
double 	kernelNS=0;			// Correction for non-specifisity
Track 	*track1=0, *track2=0, *projTrack=0;
Kernel 	*kern=0;
double 	maxNA0=99;
double 	maxZero0=99;
double 	maxNA=100;
double 	maxZero=100;
int 	nShuffle=10000;
char 	*trackName1=strdup("");
char 	*trackName2=strdup("");
double 	mannW_Z=0;
double 	mannW_p=1;
double 	smoothZ=3;

Model 	*model;

int 	threshold=0;

FILE 	*logFile=0;
bool 	doAutoCorr=0;

int 	corrScale=10;
double 	prod11=0,prod12=0,prod22=0, eprod1,eprod2;
int 	nprod=0;
XYCorrelation XYfgCorrelation;		    // array for correlation picture
XYCorrelation XYbgcorrelation;			// array for correlation picture
Fourier LCorrelation;


int 	bpType=BP_SIGNAL;
bool 	clearProfile=false;
int 	scoreType=AV_SCORE;
FileListEntry files[MAX_FILES];
int   	nfiles=0;
bool LCExists=false;

double avBg=FNA,sdBg=FNA,avFg=FNA,sdFg=FNA;

int  	pgLevel=2;
char    *biotypes=0;
float total=0;						// total count over the track

//==============================================================================
//==============================================================================
Name_Value* bpTypes[]= {
		new Name_Value("SCORE",BP_SCORE),
		new Name_Value("SIGNAL" ,BP_SIGNAL),
		new Name_Value("LOGPVAL",BP_LOGPVAL),
		0
};
Name_Value* kernelTypes[]= {
		new Name_Value("NORMAL",KERN_NORM),
		new Name_Value("LEFT_EXP",KERN_LEFT_EXP),
		new Name_Value("RIGHT_EXP",KERN_RIGHT_EXP),
		new Name_Value("CUSTOM",KERN_CUSTOM),
		0
};


Name_Value* distrTypes[]= {
		new Name_Value("NONE",DISTR_NONE),
		new Name_Value("SHORT",DISTR_SHORT),
		new Name_Value("DETAIL",DISTR_DETAIL),
		0
};


Name_Value* complFlags[]={
		new Name_Value("IGNORE_STRAND",IGNORE_STRAND),
		new Name_Value("COLLINEAR",COLLINEAR),
		new Name_Value("COMPLEMENT",COMPLEMENT),
		0
};
Name_Value* LCFlags[]={
		new Name_Value("BASE",LC_BASE),
		new Name_Value("CENTER",LC_CENTER),
		0
};
Name_Value* outWigTypes[]={
		//	correlation is ( f*\int g\rho + g*\int f\rho )
		new Name_Value("NONE",NONE),
		new Name_Value("BASE",WIG_BASE|WIG_SUM), //correlation without substract average
		new Name_Value("CENTER",WIG_CENTER|WIG_SUM),//substract average
		//	correlation is ( \int g\rho * \int f\rho )
		new Name_Value("BASE_MULT",WIG_BASE|WIG_MULT),
		new Name_Value("CENTER_MULT",WIG_CENTER|WIG_MULT),
		0
};
Name_Value* LCScaleTypes[]={
		new Name_Value("LOG",LOG_SCALE),
		new Name_Value("LIN" ,LIN_SCALE),
		0
};


Name_Value* outResTypes[]={
		new Name_Value("NONE",NONE),
		new Name_Value("XML",XML),
		new Name_Value("TAB",TAB),
		new Name_Value("BOTH",XML|TAB),
		0
};
Name_Value* PlotTypes[]={
		new Name_Value("NONE",NONE),
		new Name_Value("R",R),
		new Name_Value("PDF",PDF),
		new Name_Value("HTML",HTML),
		new Name_Value("ALL",R|PDF|HTML),
		0
};

//==============================================================================
//==============================================================================

Param *pparams[]={
//================================================== Common parameters
		new Param(AP,"common parameters"),
		new Param(AP,"v"		    ,0, &verbose	,1, "verbose"),
		new Param(AP,"syntax"		,0, &syntax		,1, "strong syntax control in input files"),
		new Param(AP,"verbose"		,0, &verbose	,   "verbose"),
		new Param(AP,"s"		    ,0, &silent		,1, "no output to stdout"),
		new Param(AP,"silent"		,0, &silent		,	"no output to stdout"),
//======================== =====================================================================================
		new Param(AP,"preparation parameters"),
		new Param(AP,"bin" 	 		,1, &binSize  		,"bin size for input averaging"),
		new Param(AP,"clear" 		,0, &clearProfile 	,"force binary profile preparation"),
		new Param(AP,"c" 	  		,0, &clearProfile 	, 1,"force  binary profile preparation"),
		new Param(SM,"smoothZ" 		,0, &smoothZ 		, "Z-Score for smoothed profile"),
//======================== =====================================================================================
		new Param(AP,"paths and files"),
		new Param(AP,"cfg" 			,0, &cfgFile 		,"config file"),
		new Param(AP,"profPath" 	,1, &profPath 		,"path for binary profiles", true),
		new Param(AP,"trackPath" 	,1, &trackPath 		,"path for tracks", true),
		new Param(BN,"binPath" 		,1, &binPath 		,"path for bined tracks", true),
		new Param(SM,"smoothPath"	,1, &smoothPath 	,"path for smoothed tracks", true),
		new Param(SG,"resPath" 		,1, &resPath 		,"path for results", true),
		new Param(SG,"report" 		,1, &reportPath		,"path for reports. relative to the resPath", true),

		new Param(AP,"confounder"	,0, &confFile		,"confounder filename"),
		new Param(AP,"aliases"		,0, &aliasFile		,"Aliase table"),

		new Param(SG,"statistics"	,0, &statFileName	,"cumulative file with statistics"),
		new Param(SG,"params" 		,0, &paramsFileName	,"cumulative file with parameters"),
		new Param(AP,"log" 			,0, &logFileName	,"cumulative log-file"),
//		new Param(AP,"id_suff" 		,0, &idSuff		,0),	// suffix for the result files
//======================== =====================================================================================
		new Param(AP, "input parameters"),
		new Param(AP, "chrom"		,1, &chromFile	,"chromosome file"),
		new Param(AP, "BufSize"		,0, &binBufSize	,"Buffer Size"),
		new Param(AP, "bpType" 		,1, &bpType 	,bpTypes	,"The value used as a score for BroadPeak input file"),
//		new Param(SG|PRJ,"pcorProfile" ,1, &pcorProfile	,"Track for partial correlation"),
		new Param(PRJ,"outPrjBGr"   ,0, &outPrjBGr	,"Write BedGraph for projections"),
		new Param(SG, "NA"       	,1, &NAFlag     ,1 , "use NA values as unknown and fill them by noise"),
		new Param(SG, "threshold"	,1, &threshold	,"threshold for input data for removing too small values: 0..250"),
//======================== =====================================================================================
		new Param(SG, "Analysis parameters"),
		new Param(SG, "kernelType"	,1, &kernelType	,kernelTypes,0),
		new Param(SG, "customKern"	,1, &customKern	,0),
		new Param(SG, "kernelSigma"	,3, &kernelSigma,"Kernel width"),
		new Param(SG, "kernelShift"	,1, &kernelShift,0),
		new Param(SG, "wSize" 	  	,3, &wSize  	,"Window size"),
		new Param(SG, "wStep" 	  	,1, &wStep  	,0),
		new Param(SG, "kernelNS"	,0, &kernelNS  	,0),
		new Param(SG, "flankSize"	,1, &flankSize  ,0),
		new Param(SG, "maxNA"		,1, &maxNA0  	,"Max number of NA values in window (percent)"),
		new Param(SG, "maxZero"		,1, &maxZero0  	,"Max number of zero values in window (percent)"),
		new Param(SG, "nShuffle"	,1, &nShuffle  	,"Number of shuffles for background calculation"),
		new Param(SG, "noiseLevel"	,1, &noiseLevel ,0),
		new Param(SG, "complFg"		,1, &complFg	,complFlags,0),
		new Param(SG, "localShuffle" ,1, &localShuffle,1,"Use cyclic permutations"),
//==============================================================================================================
		new Param(SG, "Output parameters"),
		new Param(SG, "outSpectr" 	,1, &outSpectr    ,"write fourier spectrums"),
		new Param(SG, "outChrom" 	,1, &outChrom     ,"write statistics by chromosomes"),
		new Param(SG, "writeDistr" 	,1, &writeDistr, distrTypes   ,"write foreground and background distributions"),
		new Param(SG, "plotType" 	,1, &RScriptFg,  PlotTypes    ,0),
		new Param(SG, "r" 			,0, &RScriptFg    ,R,"write R script for the result presentation"),
		new Param(SG, "crossWidth" 	,0, &crossWidth   ,0,"Width of cross-correlation plot"),
		new Param(SG, "Cross" 		,1, &writeDistCorr,1,"Write cross-correlations"),
		new Param(SG, "outLC"		,1, &outLC	,LCFlags  ,0),
		new Param(SG, "lc"			,0, &outLC		  ,	LC_BASE,"produce profile correlation"),
		new Param(SG, "LCScale"		,0, &LCScale	  ,LCScaleTypes,"Local correlation scale: LOG | LIN"),
		new Param(SG, "L_LC"		,1, &L_LC	      ,"threshold on correlation when write the local correlation"),
		new Param(SG, "R_LC"		,1, &R_LC	      ,"threshold on correlation when write the local correlation"),
		new Param(SG, "outRes" 		,0, &outRes 	  ,outResTypes,"format for results in statistics file"),
		new Param(SG, "AutoCorr"  	,1, &doAutoCorr   ,0),
		new Param(SG, "aliases"  	,1, &aliasFile    ,0),
		new Param(SG, "Rscript"   	,1, &Rscript      ,0),
		new Param(SG, "plotH"   	,1, &plotH    	  ,0),
		new Param(SG, "plotW"   	,1, &plotW    	  ,0),

//======================== =================== Additional parameters (see Undocumented) ===============================
		new Param(AP, "debug"		,0, &debugFg   	  ,0),	//debug mode
		new Param(AP, "d"			,0, &debugFg   	  ,1, 0),	//debug mode
		//===================================== ParseGenes parameters =================
		new Param(PG, "gencodeLevel",1, &pgLevel  	  ,1, 0),	//max level in ENCODE to be taken into account
		new Param(PG, "biotypes"	,1, &biotypes	  ,"Biotypes Filter"),	//minimal biotypes filter

		new Param(AP, "Happy correlations!"),
		0,
};

char zfdsgfdsID[50];
char * printId(){snprintf(zfdsgfdsID,sizeof(zfdsgfdsID), "%08lx",id); return zfdsgfdsID;}

void PrepareParams(){

	wProfSize=wSize/binSize;       		// size of widow (profile scale)
	wProfStep=wStep/binSize;       		// window step   (profile scale)

	//====================================================================== Prepare parameters
	kernelProfSigma=double(kernelSigma)/binSize;   // kernel width ((profile scale)
	kernelProfShift=double(kernelShift)/binSize;   // kernel shift ((profile scale)

	maxNA   =(int)(maxNA0  * wProfSize/100);			// rescale maxNA
	maxZero =(int)(maxZero0* wProfSize/100);			// rescale maxZero
	if(maxZero>=wProfSize) maxZero=wProfSize-1;
	if(maxNA  >=wProfSize) maxNA  =wProfSize-1;
	defFlanks(wProfSize);

	if(aliasFile !=0){
		aliases=new AliasTable(aliasFile);
	}
	//===================================================================== generate Kernels
}

void defFlanks(int l){
	LFlankProfSize=flankSize/binSize;
	int ll=nearFactor(2*LFlankProfSize+l);
	LFlankProfSize=(ll-l)/2;
	profWithFlanksLength=ll;
	RFlankProfSize=ll-l-LFlankProfSize;
	kern=MakeKernel(profWithFlanksLength);
}




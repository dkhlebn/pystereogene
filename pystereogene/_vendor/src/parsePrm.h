/*
 * parsePrm.h
 *
 *  Created on: 31 июл. 2025 г.
 *      Author: PC
 */
#ifndef PARSEPRM_H_
#define PARSEPRM_H_


struct NamedRes{
	const char *name;
	void *value;
	int type;					// parameter type
	char* (*f)();
	NamedRes(const char *nm, double *v);
	NamedRes(const char *nm, int *v);
	NamedRes(const char *nm, char **v);
	NamedRes(const char *nm, char* (*ff)());
	NamedRes(const char *nm);
	char* printValue(char *buf, int siz);
	int printValue(FILE* f);
};


struct Name_Value{			// symbolic name for a value
	const char* name;		// name for the value
	int value;				// value
	Name_Value(const char *nm, int val){name=nm; value=val;}
};


struct Param{
	const char* name;			// command line (cfg) argument name
	int type;					// parameter type
	Name_Value **enums;			// array of aviable values
	void *prm;					// pointer to the argument value
	int value;					// a value that should be set if -prm is used in a command line
	int printFg;				// the param should be printed to PRM file (1) or in statistics (3)
	int prog_fg;				// the parameter relevant to the program of given type
	const char *description;
	Param(int prog_fg,const char* descr);
	Param(int prog_fg,const char* _name, int print, int    *prm, const char* descr);
	Param(int prog_fg,const char* _name, int print, int    *prm, int val, const char* descr);
	Param(int prog_fg,const char* _name, int print, int    *prm, Name_Value **nfg, const char* descr);
	Param(int prog_fg,const char* _name, int print, bool   *prm, const char* descr);
	Param(int prog_fg,const char* _name, int print, bool   *prm, bool val, const char* descr);
	Param(int prog_fg,const char* _name, int print, double *prm, const char* descr);
	Param(int prog_fg,const char* _name, int print, char * *prm, const char* descr);
	Param(int prog_fg,const char* _name, int print, char*  *_prm, const char* descr, bool path);

	void setVal();
	void init(int prg, const char* _name,int print, void* _prm, int type, Name_Value **fg, const char* descr);
	void init(int prg, const char* _name,int print, void *_prm, int _type, const char* descr);
	void printDescr();
	int readVal(char *s);
	int readEnum(char *s);
	char* printParamValue(char *buf, int siz);
	int   printParamValue(FILE *out);
	char* printParamXML(char *buf, int siz);
};




extern Param *pparams[];
extern NamedRes *results[];
extern const char *progDescription;
extern const char *_version;
extern int prog_flag;
extern char *inFiles[256];
extern int nInFiles;

void parseArgs(int argc, char **argv);
void readConfig(const char * cfg);
void printHelp();

#endif /* PARSEPRM_H_ */

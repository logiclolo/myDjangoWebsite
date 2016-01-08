#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include "conflib.h"
#include "typedef.h"

#define MODULE_VERSION_STR "2.0.0.0"
#define MODIFY_DATETIME "2009/10/13 13:11:48"
volatile char rcsid[] = "$Id: " MODULE_VERSION_STR ",confclient," MODIFY_DATETIME " $";

void Usage(void)
{
	printf( "Software confclient II\n"
					"Usage:\n"
					"	confclient [-g XPath] [-t Type] [-p Privilege] [-b]\n"
					"	confclient [-s XPath] [-t Type] [-p Privilege] [-c] [-b]\n"
					"	confclient [-a XPath] [-t Type] [-p Privilege] [-c] [-f CFGFile]\n"
					"	confclient [-x XPath]\n"
					"	confclient [-v] [-h]\n"
					"Options:\n"
					"	-g	Get parameters value\n"
					"	-s	Set parameters value\n"
					"	-a	Apply parameters value\n"
					"	-x	Use one XPath to get one parameter value from shared memory\n"
					"	-b	Get/Set via buffer\n"
					"	-t	Type can be JavaScript, NameValue, Value, ShellScript, XML, IW, SingleQuo default=>Value\n"
					"	-p	Access security privilege, default=>0\n"
					"	-c	Check parameters value\n"
					"	-f	The XML config file\n" 
					"	-v	Display version information\n"
					"	-h	This help\n" );
}

void ShowVersion( void )
{
	printf( "Software confclient version %s\n", MODULE_VERSION_STR );
}

int main( int argc, char *argv[] )
{
	int iCh;
	char szXPath[8192];
	char szValue[1024];
	TConfOpt confopt;
	
	memset( &confopt, 0, sizeof( confopt ) );
	strcpy( confopt.szType, "NameValue" );
	while( ( iCh = getopt( argc, argv, "hvcbt:f:g:s:a:p:x:" ) ) != -1 )
	{
		switch ( iCh )
		{
			case 't':
				strcpy( confopt.szType, optarg );
				break;
			case 'f':
				strcpy( confopt.szCFGFile, optarg );
				break;
			case 'g':
				confopt.eCmd = eGetCmd;
				strcpy( szXPath, optarg );
				confopt.pszXPath = szXPath;
				break;
			case 's':
				confopt.eCmd = eSetCmd;
				strcpy( szXPath, optarg );
				confopt.pszXPath = optarg;
				break;
			case 'a':
				confopt.eCmd = eApplyCmd;
				strcpy( szXPath, optarg );
				confopt.pszXPath = optarg;
				break;
			case 'x':
				strcpy( szXPath, optarg );
				if( Configer_GetParamValueByXPath( szXPath, szValue, sizeof( szValue ) ) == S_OK )
				{
					/*printf( "%s=%s\n", szXPath, szValue );*/
					printf( "%s\n", szValue );
					return 0;
				}
				else
				{
					/*printf( "%s is invalid\n", szXPath );*/
					return -1;
				}
				break;
			case 'p':
				confopt.iPrivilege = atoi( optarg );
				break;
			case 'c':
				confopt.iCheck = 1;
				break;
			case 'b':
				confopt.iBuffer = 1;
				break;
			case 'v':
				ShowVersion();
				return -1;
				break;
			case 'h':
			default:
				Usage();
				return -1;
		}
	}
	
	if( confopt.pszXPath != NULL )
	{
		if( Configer_Control( &confopt, NULL, 0 ) == S_OK )
		{
			return 0;
		}
	}
	
	Usage();
	return -1;	
}

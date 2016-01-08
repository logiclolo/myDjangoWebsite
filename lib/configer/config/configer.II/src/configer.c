/*
 *******************************************************************************
 * $Header:$
 *
 *  Copyright (c) 2000-2010 Vivotek Inc. All rights reserved.
 *
 *  +-----------------------------------------------------------------+
 *  | THIS SOFTWARE IS FURNISHED UNDER A LICENSE AND MAY ONLY BE USED |
 *  | AND COPIED IN ACCORDANCE WITH THE TERMS AND CONDITIONS OF SUCH  |
 *  | A LICENSE AND WITH THE INCLUSION OF THE THIS COPY RIGHT NOTICE. |
 *  | THIS SOFTWARE OR ANY OTHER COPIES OF THIS SOFTWARE MAY NOT BE   |
 *  | PROVIDED OR OTHERWISE MADE AVAILABLE TO ANY OTHER PERSON. THE   |
 *  | OWNERSHIP AND TITLE OF THIS SOFTWARE IS NOT TRANSFERRED.        |
 *  |                                                                 |
 *  | THE INFORMATION IN THIS SOFTWARE IS SUBJECT TO CHANGE WITHOUT   |
 *  | ANY PRIOR NOTICE AND SHOULD NOT BE CONSTRUED AS A COMMITMENT BY |
 *  | VIVOTEK INC.                                                    |
 *  +-----------------------------------------------------------------+
 *
 * $History:$
 *
 *******************************************************************************
 */
/*!
 *******************************************************************************
 * Copyright 2000-2010 Vivotek, Inc. All rights reserved.
 *
 * \file
 * configer.c
 *
 * \brief
 * the source code of configer
 *
 * \date
 * 2009/09/07
 *
 * \author
 * Ben Chen
 *
 *******************************************************************************
 */
#include <stdio.h>
#include <expat.h>
#include <time.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/syslog.h>
#include <errno.h>
#include <sys/un.h>
#include <ctype.h>
#include <pthread.h>
#include <sys/stat.h>
#include <sys/file.h>
#include <dirent.h>
#include <signal.h>
#include <sys/msg.h>
#include <sys/ipc.h>
#include <sys/sem.h>
#include <sys/time.h>
#include <regex.h>
#include "configer.h"
#include "common.h"
#include "sxmlparser.h"
#include "message.h"
#include "swatchdog.h"
#define WATCHDOG_SVR_SCK	"/var/run/swatchdog/swatchdog.sck"

#define CONFIGER_MODULE_NAME 	"configer"
#define MODULE_VERSION_STR 		"2.0.3.1"
#define MODIFY_DATETIME 		"2015/01/27 10:00:00"
#define SOCKETPATH		"/tmp/configer"

volatile char rcsid[] = "$Id: " MODULE_VERSION_STR " " CONFIGER_MODULE_NAME " " MODIFY_DATETIME " $";

int g_iClientConnect = 0;
int g_iOutBufLen;
char g_szOutBuf[BUFFSIZE];
char *g_pszPrefixETCPath = NULL;
pthread_mutex_t pmutexSignalProcess;
pthread_mutex_t pmutexSystem;
HANDLE g_hSXMLParserCDF = NULL;
TMessageUtilOption g_tMsgUtilInfo_KickWatchDog;

BOOL g_bTerminated = FALSE;

//20101123 Added by danny For support advanced system log
BOOL IsAdvLogSupport()
{
	FILE *fp;
	char szSrch[256];

	if( (fp = fopen(SYSLOG_CONF, "r")) == NULL )
	{
		return FALSE;
	}

	while( fgets(szSrch, sizeof(szSrch), fp) != NULL )
	{
 		if( strstr(szSrch, CONFIGSET_LOG) != NULL )
 		{
			return TRUE;
 		}
	}

	return FALSE;
}

static SCODE Swatchdog_WatchPolicy(const EControlMessageType eWatchPolicy)
{
	TMessageInfo tMsgInfo;
	memset(&tMsgInfo, 0, sizeof(tMsgInfo));

	tMsgInfo.iIndex     = swdConfiger;
	tMsgInfo.iType      = eWatchPolicy;

	SCODE scRet = S_OK;

	char szBuffer[256+1] = "";
	int iBuffLen = 256;

	if (Message_Compose_Control(szBuffer, &iBuffLen, 1, &tMsgInfo) != S_OK)
	{
		syslog(LOG_WARNING, "Compose watchdog control message failed");
		scRet = S_FAIL;
	}

	TMessageUtilOption tMsgUtilInfo;
	memset(&tMsgUtilInfo, 0, sizeof(tMsgUtilInfo));

	tMsgUtilInfo.iControlType = 0;
	sprintf(tMsgUtilInfo.szSocketPath, "%s", WATCHDOG_SVR_SCK);
	tMsgUtilInfo.iBufLenOut = iBuffLen;
	memcpy(tMsgUtilInfo.pcBuffer, szBuffer, iBuffLen);

	if (Message_Util_SendbySocket(&tMsgUtilInfo) != S_OK)
	{
		syslog(LOG_WARNING, "Unable to send message");
		scRet = S_FAIL;
	}

	return scRet;
}

static SCODE Swatchdog_Message_Compose_KickWatchDog()
{
	TMessageInfo tMsgInfo;
	memset(&tMsgInfo, 0, sizeof(tMsgInfo));

	tMsgInfo.iIndex     = swdConfiger;
	tMsgInfo.iType      = cmKickWatchDog;

	SCODE scRet = S_OK;

	char szBuffer[256+1] = "";
	int iBuffLen = 256;

	if (Message_Compose_Control(szBuffer, &iBuffLen, 1, &tMsgInfo) != S_OK)
	{
		syslog(LOG_WARNING, "Compose watchdog control message failed");
		scRet = S_FAIL;
	}

	memset(&g_tMsgUtilInfo_KickWatchDog, 0, sizeof(g_tMsgUtilInfo_KickWatchDog));
	g_tMsgUtilInfo_KickWatchDog.iControlType = 0;
	sprintf(g_tMsgUtilInfo_KickWatchDog.szSocketPath, "%s", WATCHDOG_SVR_SCK);
	g_tMsgUtilInfo_KickWatchDog.iBufLenOut = iBuffLen;
	memcpy(g_tMsgUtilInfo_KickWatchDog.pcBuffer, szBuffer, iBuffLen);

	return scRet;
}

static SCODE Swatchdog_KickWatchdog()
{
	struct timeval tv;
	static struct timeval prev_tv;
	SCODE scRet = S_OK;

	gettimeofday(&tv, NULL);
	DWORD dwTimeDifference = (tv.tv_sec * 1000000 + tv.tv_usec) - (prev_tv.tv_sec * 1000000 + prev_tv.tv_usec);
	if (dwTimeDifference > 10000000)
	{
		// kick every 10 second
		//scRet = Swatchdog_WatchPolicy(cmKickWatchDog);
		if (Message_Util_SendbySocket(&g_tMsgUtilInfo_KickWatchDog) != S_OK)
		{
			syslog(LOG_WARNING, "Unable to send message");
			scRet = S_FAIL;
		}
		prev_tv = tv;
	}
	return scRet;

}

static SCODE Swatchdog_StartWatchMe()
{
	return Swatchdog_WatchPolicy(cmEnrollWatchDog);
}

static SCODE Swatchdog_StopWatchMe()
{
	return Swatchdog_WatchPolicy(cmUnloadWatchDog);
}

int CreateUnixSocket( const char *pszPath )
{
	struct sockaddr_un sunx;
	int iFD;

	if( pszPath[0] == '\0')
	{
		return -1;
	}

	(void) unlink( pszPath );

	memset( &sunx, 0, sizeof( sunx ) );
	sunx.sun_family = AF_UNIX;
	(void) strncpy( sunx.sun_path, pszPath, sizeof( sunx.sun_path ) - 1 );
	iFD = socket( AF_UNIX, SOCK_STREAM, 0 );

	// SET SOCKET REUSE Address
	int sock_opt = 1;
	if (setsockopt(iFD, SOL_SOCKET, SO_REUSEADDR, (void*)&sock_opt, sizeof(sock_opt) ) == -1){
		return false;
	}
	fcntl(iFD, F_SETFL, O_NONBLOCK);
	if( ( iFD < 0 ) ||
		  ( bind( iFD, (struct sockaddr *) &sunx, sizeof( sunx.sun_family ) + strlen( sunx.sun_path ) ) < 0 ) ||
	    ( chmod( pszPath, 0666 ) < 0 ) )
	{
		printf( "cannot create %s (%d).%s\n", pszPath, errno, strerror( errno ) );
		close( iFD );
		return -1;
	}
	return iFD;
}
void SetModifyTime()
{
	char szModifyTime[32];
	struct timeval tvModifyTime;

	gettimeofday(&tvModifyTime, NULL);
	sprintf( szModifyTime, "%d", (DWORD)tvModifyTime.tv_sec );
	SXMLParser_SetTagValueByXPath( g_hSXMLParserCDF, "root_modifytime_value", szModifyTime );
}

SCODE ParseCmd( const char *pszCmdBuf )
{
	char *pszNext = NULL;
	char *pszValue = NULL;
	char *pszSrch;
	char *pszXPath = g_Cmd.szXPath;
	int i;
	const TXMLElement *pElement;

	memset( &g_Cmd, 0, sizeof( g_Cmd ) );
	sscanf( pszCmdBuf, "%s", g_Cmd.szMethod);
	g_Cmd.iOption = 0;
	if( strcmp( g_Cmd.szMethod, "get" ) == 0 )
	{
		sscanf( pszCmdBuf, "%s %s %d %d", g_Cmd.szMethod, g_Cmd.szType, &g_Cmd.iPrivilege, &g_Cmd.iBuf );
	}
	else if( strcmp( g_Cmd.szMethod, "set" ) == 0 )
	{
		sscanf( pszCmdBuf, "%s %s %d %d %d", g_Cmd.szMethod, g_Cmd.szType, &g_Cmd.iPrivilege, &g_Cmd.iCheck, &g_Cmd.iBuf );
		g_Cmd.iOption = CMD_OPT_PROCESS|CMD_OPT_SIGNAL|CMD_OPT_MESSAGE;
	}
	else if( strcmp( g_Cmd.szMethod, "apply" ) == 0 )
	{
		sscanf( pszCmdBuf, "%s %s %d %d %s", g_Cmd.szMethod, g_Cmd.szType, &g_Cmd.iPrivilege, &g_Cmd.iCheck, g_Cmd.szCFGFile );
	}
	else
	{
		return S_FAIL;
	}

	pszSrch = strchr( pszCmdBuf, '\n' );
	if( pszSrch == NULL )
	{
		return S_FAIL;
	}
	else
	{
		pszSrch++;
	}
	pszNext = pszSrch - 1;
	do
	{
		pszNext++;
		g_Cmd.iNum++;
	}
	while( ( pszNext = strchr( pszNext, '&') ) != NULL );
	if( g_Cmd.iNum > CMD_MAX_NUM )
	{
		printf( "g_Cmd.iNum > CMD_MAX_NUM\n" );
		return S_FAIL;
	}

	if( ( strchr( pszSrch, '\0' ) - pszSrch + 5*g_Cmd.iNum + 2 ) > sizeof( g_Cmd.szXPath ) )
	{
		return -1;
	}

	if( strncmp( pszSrch, CMD_OPTION, strlen(CMD_OPTION) ) == 0 )
	{
		if( ( pszNext = strchr( pszSrch, '&' ) ) == NULL )
		{
			pszNext = strchr( pszSrch, '\0' );
		}

		if( ( pszValue = strchr( pszSrch, '=' ) ) != NULL && ( pszValue < pszNext ) )
		{
			g_Cmd.iOption = atoi( pszValue + 1 );
			pszSrch = pszNext + 1;
		}
	}
	printf( "%s%d\n", CMD_OPTION, g_Cmd.iOption );

	if( strncmp( pszSrch, "root", 5) == 0 && strcmp( g_Cmd.szMethod, "set" ) != 0)
	{
		strcpy( pszXPath, pszSrch );
		g_Cmd.pszXPath[0] = pszXPath;
	}
	else
	{
		for( i = 0; i < g_Cmd.iNum; i++ )
		{
			if( ( pszNext = strchr( pszSrch, '&' ) ) == NULL )
			{
				pszNext = strchr( pszSrch, '\0' );
			}
			g_Cmd.pszXPath[i] = pszXPath;

			if( ( pszValue = strchr( pszSrch, '=' ) ) == NULL || ( pszValue > pszNext ) )
			{
				strcpy( pszXPath, "root_");
				pszXPath += 5;
				memcpy( pszXPath, pszSrch, pszNext - pszSrch );
				pszXPath += pszNext - pszSrch + 1;
				pszSrch = pszNext + 1;
				printf( "xpath[%d]:%s\n", i, g_Cmd.pszXPath[i] );
			}
			else
			{
				strcpy( pszXPath, "root_");
				pszXPath += 5;
				memcpy( pszXPath, pszSrch, pszValue - pszSrch );
				pszXPath += pszValue - pszSrch + 1;
	  		pszSrch = pszValue + 1;
	  		g_Cmd.pszValue[i] = pszXPath;
				memcpy( pszXPath, pszSrch, pszNext - pszSrch );
				pszXPath += pszNext - pszSrch + 1;
				pszSrch = pszNext + 1;
				printf( "xpath[%d]:%s=%s\n", i, g_Cmd.pszXPath[i], g_Cmd.pszValue[i] );
			}

			if( ( pElement = SXMLParser_GetElementByXPath( g_hSXMLParserCDF, g_Cmd.pszXPath[i] ) ) == NULL )
			{
				printf( "%s is invalid\n", g_Cmd.pszXPath[i] );
				i--;
				g_Cmd.iNum--;
			}
			else if( strcmp( g_Cmd.szMethod, "set" ) == 0 )
			{
				if( g_Cmd.pszValue[i] == NULL )
				{
					printf( "%s hasn't value\n", g_Cmd.pszXPath[i] );
					i--;
					g_Cmd.iNum--;
				}
				else
				{
					pElement = pElement->pChild;
					for( ; pElement!=NULL; pElement = pElement->pSibling )
					{
						if( ( strncmp( pElement->pszTagName, "value", 6 ) == 0 ) || ( strncmp( pElement->pszTagName, "aliasxpath", 11 ) == 0 ) )
						{
							break;
						}
					}
					if( pElement == NULL )
					{
						printf( "%s is invalid\n", g_Cmd.pszXPath[i] );
						i--;
						g_Cmd.iNum--;
					}
				}
			}
		}
	}
	if( g_Cmd.iNum > 0 )
	{
		if( ( strcmp( g_Cmd.szMethod, "set" ) == 0 ) || ( strcmp( g_Cmd.szMethod, "apply" ) == 0 ) )
		{
			SetModifyTime();
		}
		return S_OK;
	}
	else
	{
		return S_FAIL;
	}
}

int CheckXPath( const char *pszXPath)
{
	int i;
	const char *pcXPath;
	const char *pcCmdXPath;

	for( i = 0; i < g_Cmd.iNum; i++ )
	{
		pcXPath = pszXPath;
		pcCmdXPath = g_Cmd.pszXPath[i];
		while( ( *pcXPath == *pcCmdXPath ) && ( *pcXPath != '\0' ) )
		{
			pcXPath++;
			pcCmdXPath++;
		}

		if( ( *pcXPath == '\0' ) && ( *pcCmdXPath == '\0' ) )
		{
			return i;
		}
		else if( ( *pcXPath == '\0' ) && ( *pcCmdXPath == '_' ) )
		{
			return i;
		}
		else if( ( *pcXPath == '_' ) && ( *pcCmdXPath == '\0' ) )
		{
			return i;
		}
	}
//	printf( "check xpath %c, %c\n", pcXPath, pcCmdXPath );

	return -1;
}

void OutputData( const char *szData, EOutputType EType )
{
	const char *pszInput;
	switch( EType )
	{
		case StartTagType:
			if( strncmp( g_Cmd.szType, "XML", 4 ) == 0 )
			{
				g_iOutBufLen += sprintf( g_szOutBuf + g_iOutBufLen, "<%s>", szData );
			}
			break;
		case EndTagType:
			if( strncmp( g_Cmd.szType, "XML", 4 ) == 0 )
			{
				g_iOutBufLen += sprintf( g_szOutBuf + g_iOutBufLen, "</%s>", szData );
			}
			break;
		case XPathType:
			if( ( strncmp( g_Cmd.szType, "Value", 6 ) != 0 ) && ( strncmp( g_Cmd.szType, "XML", 4 ) != 0 ) )
			{
				g_iOutBufLen += sprintf( g_szOutBuf + g_iOutBufLen, "%s=", szData );
			}
			break;
		case ValueType:
			if( strncmp( g_Cmd.szType, "JavaScript", 11 ) == 0 )
			{
				g_iOutBufLen += sprintf( g_szOutBuf + g_iOutBufLen, "\'" );
		  	pszInput = szData;
		  	while ( *pszInput != '\0' )
				{
					if ( *pszInput == '\\' )
					{
		  			*( g_szOutBuf + g_iOutBufLen++ )='\\';
		  		}
		  		*( g_szOutBuf + g_iOutBufLen++ ) = *pszInput++;
		  	}
		  	g_iOutBufLen += sprintf( g_szOutBuf + g_iOutBufLen, "\'\r\n" );
		  }
		  else if( ( strncmp( g_Cmd.szType, "NameValue", 10 ) == 0 ) || ( strncmp( g_Cmd.szType, "Value", 6 ) == 0 ) )
		  {
		  	g_iOutBufLen += sprintf( g_szOutBuf + g_iOutBufLen, "%s\n", szData );
			}
			else if( strncmp( g_Cmd.szType, "ShellScript", 12 ) == 0 )
		  {
		  	g_iOutBufLen += sprintf( g_szOutBuf + g_iOutBufLen, "\"%s\"\n", szData );
			}
			else if( strncmp( g_Cmd.szType, "SingleQuo", 10 ) == 0 )
		  {
		  	g_iOutBufLen += sprintf( g_szOutBuf + g_iOutBufLen, "\'%s\'\n", szData );
			}
			else if( strncmp( g_Cmd.szType, "IW", 3 ) == 0 )
		  {
		  	g_iOutBufLen += sprintf( g_szOutBuf + g_iOutBufLen, "\'%s\'\r\n", szData );
			}
			else
			{
				g_iOutBufLen += sprintf( g_szOutBuf + g_iOutBufLen, "%s", szData );
			}
	}
}

SCODE CheckNumber( const char *pszCheck, const char *pszValue)
{
	const char *pszStart = NULL;
	const char *pszEnd = NULL;
	const char *pszTmp = NULL;
	const char *pszMin;
	const char *pszMax;
	char szCmpValue[32];
	char szLimit[50];
	int iLen = 0;
	int iHasMin;
	int iHasMax;
	int iMin=0;
	int iMax=0;
	int iValue;

	pszStart = pszCheck;
	printf( "CheckNumber %s %s \n", pszCheck, pszValue );
	while( ( *pszValue == '0' ) && ( strlen(pszValue) > 1 ) )
	{
		pszValue++;
	}
	iValue = atoi( pszValue );
	sprintf( szCmpValue, "%d", iValue );
	if( strcmp( pszValue, szCmpValue ) != 0 )
	{
		return S_FAIL;
	}
	while( ( pszEnd = strchr( pszStart, ',' ) ) != NULL && ( pszEnd < pszCheck + strlen( pszCheck ) ) )
	{
		iLen = pszEnd - pszStart;
		memcpy( szLimit, pszStart, iLen );
		szLimit[ iLen ] = '\0';
		printf( "Limit=%s Value=%d\n", szLimit, iValue );
		pszTmp = strchr( szLimit, '~' );
		iHasMax = iHasMin = 0;
		if( pszTmp == NULL )
		{
			if( atoi( szLimit ) == iValue )
			{
				printf( "match %d\n", iValue );
				return S_OK;
			}
		}
		else if( pszTmp > szLimit && strlen( pszTmp ) > 1 )
		{
			pszMin = strtok( szLimit, "~" );
			pszMax = pszTmp + 1;
			iMin = atoi( pszMin );
			iHasMin = 1;
			iMax = atoi( pszMax );
			iHasMax = 1;
			printf( "Min=%d, Max=%d\n", iMin, iMax );
		}
		else if( pszTmp > szLimit )
		{
			pszMin = strtok( szLimit, "~" );
			iMin = atoi( pszMin );
			iHasMin = 1;
			printf( "Min=%d\n", iMin );
		}
		else if( strlen( pszTmp ) > 1 )
		{
			pszMax = strtok( szLimit, "~" );
			iMax = atoi( pszMax );
			iHasMax = 1;
			printf( "Max=%d\n", iMax );
		}
		//printf( "HasMin=%d, HasMax=%d\n", iHasMin, iHasMax );
		if( ( iHasMin == 1 ) && ( iHasMax == 1 ) )
		{
			if( ( iValue >= iMin ) && ( iValue <= iMax ) )
			{
				return S_OK;
			}
		}
		else if( iHasMin == 1 )
		{
			if( iValue >= iMin )
			{
				return S_OK;
			}
		}
		else if( iHasMax == 1 )
		{
			if( iValue <= iMax )
			{
				return S_OK;
			}
		}

		pszStart = pszEnd + 1;
	}
	return S_FAIL;
}

SCODE CheckString( const char *pszCheck, const char *pszValue )
{
	const char *pszStart = NULL;
	const char *pszEnd = NULL;
	const char *pszTmp = NULL;
	const char *pszMin;
	const char *pszMax;
	char szLimit[50];
	int iLen = 0;
	int iHasMin = 0;
	int iHasMax = 0;
	int iMin = 0;
	int iMax = 0;
	int iValue = 0;

	iValue = strlen( pszValue );
	pszStart = pszCheck;
	printf( "CheckString %s %s \n", pszCheck, pszValue );
	while( ( pszEnd = strchr( pszStart, ',' ) ) != NULL && ( pszEnd < pszCheck + strlen( pszCheck ) ) )
	{
		iLen = pszEnd - pszStart;
		memcpy( szLimit, pszStart, iLen );
		szLimit[ iLen ] = '\0';
		printf( "Limit=%s Value=%d\n", szLimit, iValue );
		pszTmp = strchr( szLimit, '~' );
		iHasMax = iHasMin = 0;
		if( pszTmp == NULL )
		{
			if( atoi( szLimit ) == iValue )
			{
				printf( "match %d\n", iValue );
				return S_OK;
			}
		}
		else if( ( pszTmp > szLimit ) && ( strlen( pszTmp ) > 1 ) )
		{
			pszMin = strtok( szLimit, "~" );
			pszMax = pszTmp + 1;
			//printf( "Max=%s, Min=%s\n", pszMax, pszMin );
			iMin = atoi( pszMin );
			iHasMin = 1;
			iMax = atoi( pszMax );
			iHasMax = 1;
			printf( "Min=%d, Max=%d\n", iMin, iMax );
		}
		else if( pszTmp > szLimit )
		{
			pszMin = strtok( szLimit, "~" );
			iMin = atoi( pszMin );
			iHasMin = 1;
			printf( "Min=%d\n", iMin );
		}
		else if( strlen( pszTmp ) > 1 )
		{
			pszMax = strtok( szLimit, "~" );
			iMax = atoi( pszMax );
			iHasMax = 1;
			printf( "Max=%d\n", iMax );
		}
		//printf( "HasMin=%d, HasMax=%d\n", iHasMin, iHasMax );
		if( ( iHasMin == 1 ) && ( iHasMax == 1 ) )
		{
			if( ( iValue >= iMin ) && ( iValue <= iMax ) )
			{
				return S_OK;
			}
		}
		else if( iHasMin == 1 )
		{
			if( iValue >= iMin )
			{
				return S_OK;
			}
		}
		else if( iHasMax == 1 )
		{
			if( iValue <= iMax )
			{
				return S_OK;
			}
		}

		pszStart = pszEnd + 1;
	}
	return S_FAIL;
}

SCODE CheckEnum( const char *pszCheck, const char *pszValue )
{
	const char *pszStart = pszCheck;
	const char *pszEnd = NULL;
	char szLimit[50];
	int iLen = 0;

	printf( "CheckEnum %s %s \n", pszCheck, pszValue );
	while( ( pszEnd = strchr( pszStart, ',' ) ) != NULL && ( pszEnd < pszCheck + strlen( pszCheck ) ) )
	{
		iLen = pszEnd - pszStart;
		memcpy( szLimit, pszStart, iLen );
		szLimit[ iLen ] = '\0';
		printf( "Limit=%s Value=%s\n", szLimit, pszValue );
		if( strcmp( szLimit, pszValue ) == 0 )
		{
			printf( "match %s\n", pszValue );
			return S_OK;
		}
		pszStart = pszEnd + 1;
	}
	return S_FAIL;
}

SCODE CheckMultiple( const char *pszCheck, const char *pszValue )
{
	char szCmpValue[32];
	const char *pszStart = pszCheck;
	const char *pszEnd = NULL;
	char szLimit[50];
	int iLen = 0;
	int iValue;
	int iDivisor;

	printf( "CheckMultiple %s %s \n", pszCheck, pszValue );
	iValue = atoi( pszValue );
	sprintf( szCmpValue, "%d", iValue );
	if( ( iValue < 1 ) || ( strcmp( pszValue, szCmpValue ) != 0 ) )
	{
		return S_FAIL;
	}

	while( ( pszEnd = strchr( pszStart, ',' ) ) != NULL && ( pszEnd < pszCheck + strlen( pszCheck ) ) )
	{
		iLen = pszEnd - pszStart;
		memcpy( szLimit, pszStart, iLen );
		szLimit[ iLen ] = '\0';
		printf( "Limit=%s Value=%s\n", szLimit, pszValue );
		if( ( ( iDivisor = atoi( szLimit ) ) > 0 ) && ( iValue % iDivisor == 0 ) )
		{
			printf( "match %s\n", pszValue );
			return S_OK;
		}
		pszStart = pszEnd + 1;
	}
	return S_FAIL;
}

SCODE CheckRegularExpression( const char *pszCheck, const char *pszValue )
{
	fprintf(stderr, "%s '%s', '%s' \n", __func__, pszCheck, pszValue);
	regex_t preg; memset(&preg, 0, sizeof(preg));

	SCODE scReturn = S_OK;
	char acCheck[512] = "";

	// pszCheck will be appended ',' at the end of the string automatically
	strncpy(acCheck, pszCheck, strlen(pszCheck)-1);

	if (regcomp(&preg, acCheck, REG_EXTENDED | REG_NOSUB) != 0)
	{
		fprintf(stderr, "regex '%s' compile error\n", acCheck);
		return S_FAIL;
	}
	if (regexec(&preg, pszValue, 0, NULL, 0) != 0)
	{
		fprintf(stderr, "format mismatch (input '%s')\n", pszValue);
		scReturn = S_FAIL;
	}

	regfree(&preg); // no return vale

	return scReturn;

}

SCODE CheckValue( const char *pszCheck, const char *pszValue )
{
	char szType[ 100 ];
	char szLimit[ LIMITED_NUM ][ 100 ];
	char szPart[ LIMITED_NUM ][ VALUESIZE ];
	const char *pszStart = NULL;
	const char *pszEnd = NULL;
	int iNum = 0;
	int i = 0;
	int iLen;
	ECheckRules eType[ LIMITED_NUM ];

	//get type from szcheck
	pszStart = pszCheck;
	pszStart = strchr( pszStart, '"' );
	pszEnd = strchr( pszStart + 1, '"' );
	iLen = pszEnd - pszStart - 1;
	memcpy( szType, pszStart + 1, iLen );
	szType[ iLen ] = '\0';
	printf( "type=%s\n", szType );

	//get limit from szcheck
	pszStart = pszEnd + 1;
	while( ( pszStart = strchr( pszStart, '"' ) ) != NULL && ( pszStart < pszCheck + strlen( pszCheck ) ) )
	{
		pszEnd = strchr( pszStart + 1, '"' );
		if( pszEnd == NULL )
		{
			break;
		}
		iLen = pszEnd - pszStart - 1;
		memcpy( szLimit[iNum], pszStart + 1, iLen );
		szLimit[iNum][iLen] = ',';
		szLimit[iNum][iLen+1] = '\0';
		printf( "limit[%d]=%s\n", iNum, szLimit[iNum] );
		iNum++;
		pszStart = pszEnd + 1;
	}

	pszStart = szType;
	while( ( pszEnd = strchr( pszStart, '%' ) ) != NULL && ( pszEnd < szType + strlen( szType ) ) )
	{
		iLen = pszEnd - pszStart;
		memcpy( szPart[i], pszStart, iLen );
		szPart[i][iLen] = '\0';
		pszStart = pszEnd + 2;
		switch( *(pszEnd+1) )
		{
			case 'd':
				eType[i] = eCheckByNumber;
				break;

			case 's':
				eType[i] = eCheckByStringLength;
				break;

			case 'e':
				eType[i] = eCheckByEnumerate;
				break;

			case 'm':
				eType[i] = eCheckByMultiple;
				break;

			case 'r':
				eType[i] = eCheckByRegularExpression;
				break;
		}
		printf( "part[%d]=%s\n", i, szPart[i] );
		i++;
	}

	if( i != iNum )
	{
		return S_FAIL;
	}
	strncpy( szPart[i], pszStart, sizeof( szPart[i] ) - 1 );

	if( strlen( szPart[0] ) != 0 )
	{
		if( strncmp( pszValue, szPart[0], strlen( szPart[0]) ) != 0 )
		{
			return S_FAIL;
		}
	}
	pszStart = pszValue + strlen( szPart[0] );
	for( i = 1; i <= iNum; i++ )
	{
		//printf( "strstr=%d %s %s\n", strstr( pszStart, szPart[i]), szPart[i], pszStart );
		if( strlen( szPart[i]) != 0 )
		{
			if( ( pszEnd = strstr( pszStart, szPart[i] ) ) == 0 || pszEnd > ( pszValue + strlen( pszValue ) ) )
			{
				return S_FAIL;
			}
		}
		else
		{
			pszEnd = pszValue + strlen( pszValue );
		}
		iLen = pszEnd - pszStart;
		memcpy( szPart[i-1], pszStart, iLen );
		szPart[i-1][iLen] = '\0';
		pszStart = pszEnd + strlen( szPart[i] );
		printf( "part[%d]=%s\n", i-1, szPart[i-1] );
	}

	for( i = 0; i < iNum; i++ )
	{
		switch( eType[i] )
		{
			case eCheckByNumber:
				if ( CheckNumber( szLimit[i], szPart[i] ) != S_OK)
				{
					return S_FAIL;
				}
				break;
			case eCheckByStringLength:
				if ( CheckString( szLimit[i], szPart[i] ) != S_OK)
				{
					return S_FAIL;
				}
				break;
			case eCheckByEnumerate:
				if ( CheckEnum( szLimit[i], szPart[i] ) != S_OK)
				{
					return S_FAIL;
				}
				break;
			case eCheckByMultiple:
				if ( CheckMultiple( szLimit[i], szPart[i] ) != S_OK)
				{
					return S_FAIL;
				}
				break;
			case eCheckByRegularExpression:
				if ( CheckRegularExpression( szLimit[i], szPart[i]) != S_OK)
				{
					return S_FAIL;
				}break;
		}
	}
	return S_OK;
}

static int copy (const char* pcSrc, const char* pcDest)
{
	int inF = 0;
	int ouF = 0;
	int bytes;
	char line[4096] = "";
	int iReturn = -1;
	mode_t mode = S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH;

	if ((inF = open(pcSrc, O_RDONLY)) == -1) {
		syslog(LOG_WARNING, "[%s] unable to open source file '%s' (%s)\n", __func__, pcSrc, strerror(errno));
		goto lEND;
	}

	if ((ouF = open(pcDest, O_WRONLY | O_CREAT | O_TRUNC, mode)) == -1) {
		syslog(LOG_WARNING, "[%s] unable to open destination file '%s' (%s)\n", __func__, pcSrc, strerror(errno));
		goto lEND;
	}

	while((bytes = read(inF, line, sizeof(line))) > 0)
		write(ouF, line, bytes);

	iReturn = 1;
lEND:
	close(inF);
	close(ouF);

	return iReturn;
}

void Usage(void)
{
	printf("Software Configer II\n"
		   "Usage:\n"
		   "    configer [-i CDF_FILE] [-d] [-v] [-h]\n"
		   "Options:\n"
		   "    -i            The config description file\n"
		   "    -f            The addition directory of the config description files\n"
		   "    -d            Run in daemon\n"
		   "    -e            The prefix path of etc (special usage for Configerator)\n"
		   "    -v            Display version information\n"
		   "    -h            This help\n");
	exit(1);
}

void ShowVersion(void)
{
	printf( "Software Configer version %s\n", MODULE_VERSION_STR );
	exit(1);
}

void *SendSignalAndRunProcess( void *Arg )
{
	pid_t Pid;
	FILE *fpPidFile;
	char szValue[VALUESIZE];
	while(1)
	{
		//printf("ClientConnect=%d\n", g_iClientConnect);
		if( g_iClientConnect == 0 )
		{
			if( g_Sig.iNum > 0 )
			{
				pthread_mutex_lock( &pmutexSignalProcess );
				g_Sig.iNum--;
				pthread_mutex_lock( &pmutexSystem );
				fpPidFile = fopen( g_Sig.szPidFile[0], "r" );
				if( fpPidFile != NULL )
				{
					fscanf( fpPidFile, "%d", &Pid );
					fclose( fpPidFile );
					kill( Pid, atoi( g_Sig.szValue[0] ) );
					printf( "send signal pid=%d, sig=%s\n", Pid, g_Sig.szValue[0] );
				}
				pthread_mutex_unlock( &pmutexSystem );
				memcpy( g_Sig.szPidFile[0], g_Sig.szPidFile[1], sizeof( g_Sig.szPidFile[0] ) * ( MAX_SIGNAL_NUM - 1 ) );
				memcpy( g_Sig.szValue[0], g_Sig.szValue[1], sizeof( g_Sig.szValue[0] ) * ( MAX_SIGNAL_NUM - 1 ) );
				pthread_mutex_unlock( &pmutexSignalProcess );
			}
			if( g_Process.iNum > 0 )
			{
				pthread_mutex_lock( &pmutexSignalProcess );
				g_Process.iNum--;
				printf( "run process %s\n", g_Process.szValue[0] );
				strncpy( szValue, g_Process.szValue[0], sizeof( szValue ) - 1 );
				memcpy( g_Process.szValue[0], g_Process.szValue[1], sizeof( g_Process.szValue[0] ) * ( MAX_PROCESS_NUM - 1 ) );
				pthread_mutex_unlock( &pmutexSignalProcess );
				system( szValue );
			}
		}
		Swatchdog_KickWatchdog();
		sleep(1);
	}
	return NULL;
}

//Only accept replacement with the same strlen 
void ReplaceTagName( TXMLElement *pElement, const char* szBeforeTag, const char *szAfterTag)
{
	//strictly check
	if (strlen(szBeforeTag) != strlen(szAfterTag)) 
	{
		printf("Cannot replace!\n");
		return;
	}
	if( pElement->pParent != NULL )
	{
		pElement = pElement->pParent;
		pElement = pElement->pChild;
	}

	while( 1 )
	{
		if( strncmp( pElement->pszTagName, szBeforeTag, strlen(szBeforeTag)+1 ) == 0 )
		{
			memcpy( (void*)pElement->pszTagName, szAfterTag, strlen(szBeforeTag) );
		}

		if( pElement->pSibling == NULL )
		{
			break;
		}
		else
		{
			pElement = pElement->pSibling;
		}
	}
}

void GetCDFParam( TXMLElement *pElement, TCDFParam *pCDFParam)
{
	/*int tmp[128]; */
	pCDFParam->pszValue = (char *)pElement->pszTagValue;
	if( pElement->pParent != NULL )
	{
		pElement = pElement->pParent;
		pElement = pElement->pChild;
	}

	while( 1 )
	{
		if( strncmp( pElement->pszTagName, "cfgfile", 8 ) == 0 )
		{
			/*sprintf(tmp,"%s%s", "/home/logic.lo/project/onefw/trunk/flashfs_base/FD9171", pElement->pszTagValue);*/
			/*pCDFParam->pszCFGFile = tmp;*/
			pCDFParam->pszCFGFile = pElement->pszTagValue;
		}
		else if( strncmp( pElement->pszTagName, "seclevel", 9 ) == 0 )
		{
			pCDFParam->pszSecLevel = pElement->pszTagValue;
		}
		else if( strncmp( pElement->pszTagName, "process", 8 ) == 0 )
		{
			pCDFParam->pszProcess = pElement->pszTagValue;
		}
		else if( strncmp( pElement->pszTagName, "pidfile", 8 ) == 0 )
		{
			pCDFParam->pszPidFile = pElement->pszTagValue;
		}
		else if( strncmp( pElement->pszTagName, "sig", 4 ) == 0 )
		{
			pCDFParam->pszSig = pElement->pszTagValue;
		}
		else if( strncmp( pElement->pszTagName, "msgkey", 7 ) == 0 )
		{
			pCDFParam->pszMsgKey = pElement->pszTagValue;
		}
		else if( strncmp( pElement->pszTagName, "check", 6 ) == 0 )
		{
			pCDFParam->pszCheck = pElement->pszTagValue;
		}
		else if( strncmp( pElement->pszTagName, "keyword", 8 ) == 0 )
		{
			pCDFParam->pszKeyword = pElement->pszTagValue;
		}
		else if( strncmp( pElement->pszTagName, "get", 4 ) == 0 )
		{
			pCDFParam->pszGet = pElement->pszTagValue;
		}
		else if( strncmp( pElement->pszTagName, "getonce", 8 ) == 0 )
		{
			pCDFParam->pszGetOnce = pElement->pszTagValue;
		}
		else if( strncmp( pElement->pszTagName, "set", 4 ) == 0 )
		{
			pCDFParam->pszSet = pElement->pszTagValue;
		}
		else if( strncmp( pElement->pszTagName, "aliasxpath", 11 ) == 0 )
		{
			pCDFParam->pszAliasXPath = pElement->pszTagValue;
		}

		if( pElement->pSibling == NULL )
		{
			break;
		}
		else
		{
			pElement = pElement->pSibling;
		}
	}

	while( (pElement = pElement->pParent) != NULL )
	{
		if( pElement->pParent != NULL )
		{
			pElement = pElement->pParent;
			pElement = pElement->pChild;
		}

		while( 1 )
		{
			if( ( pCDFParam->pszCFGFile == NULL ) && ( strncmp( pElement->pszTagName, "cfgfile", 8 ) == 0 ) )
			{
				/*sprintf(tmp,"%s%s", "/home/logic.lo/project/onefw/trunk/flashfs_base/FD9171", pElement->pszTagValue);*/
				/*pCDFParam->pszCFGFile = tmp;*/
				pCDFParam->pszCFGFile = pElement->pszTagValue;
			}
			else if( ( pCDFParam->pszSecLevel == NULL ) && ( strncmp( pElement->pszTagName, "seclevel", 9 ) == 0 ) )
			{
				pCDFParam->pszSecLevel = pElement->pszTagValue;
			}
			else if( ( pCDFParam->pszParentProcess == NULL ) && ( strncmp( pElement->pszTagName, "process", 8 ) == 0 ) )
			{
				pCDFParam->pszParentProcess = pElement->pszTagValue;
			}
			else if( ( pCDFParam->pszPidFile == NULL ) && ( strncmp( pElement->pszTagName, "pidfile", 8 ) == 0 ) )
			{
				pCDFParam->pszPidFile = pElement->pszTagValue;
			}
			else if( ( pCDFParam->pszSig == NULL ) && ( strncmp( pElement->pszTagName, "sig", 4 ) == 0 ) )
			{
				pCDFParam->pszSig = pElement->pszTagValue;
			}
			else if( ( pCDFParam->pszMsgKey == NULL ) && ( strncmp( pElement->pszTagName, "msgkey", 7 ) == 0 ) )
			{
				pCDFParam->pszMsgKey = pElement->pszTagValue;
			}

			if( pElement->pSibling == NULL )
			{
				break;
			}
			else
			{
				pElement = pElement->pSibling;
			}
		}
	}
#if 0
	printf( "cfgfile=%s\n", pCDFParam->pszCFGFile );
	printf( "seclevel=%s\n", pCDFParam->pszSecLevel );
	printf( "parent process=%s\n", pCDFParam->pszParentProcess );
	printf( "process=%s\n", pCDFParam->pszProcess );
	printf( "pidfile=%s\n", pCDFParam->pszPidFile );
	printf( "sig=%s\n", pCDFParam->pszSig );
	printf( "msgkey=%s\n", pCDFParam->pszMsgKey );
	printf( "check=%s\n", pCDFParam->pszCheck );
	printf( "keyword=%s\n", pCDFParam->pszKeyword );
	printf( "set=%s\n", pCDFParam->pszSet );
	printf( "get=%s\n", pCDFParam->pszGet );
	printf( "value=%s\n", pCDFParam->pszValue );
#endif
}

SCODE ReadCFGFile( const char *pszCFGFile, const char *pszKeyword, char *pszOutValue )
{
	FILE *fpCFG;
	char szSrch[256];
	char *pszNext = NULL;
	char *pszValue = NULL;
	char *pszEnd = NULL;

	fpCFG = fopen( pszCFGFile, "r" );
	if( fpCFG == NULL )
	{
		printf( "Fail to open CFG_file:%s\n", pszCFGFile );
		syslog( LOG_ALERT, "Fail to open CFG_file:%s", pszCFGFile );
		return S_FAIL;
	}

	while( fgets( szSrch, 256, fpCFG ) != NULL )
	{
		//printf( "%s keyword=%s\n", szSrch, pszKeyword );
		if( ( pszNext = strchr( szSrch, '=' ) ) != NULL )
			*pszNext=' ';
		if( ( pszNext = strchr( szSrch, ' ' ) ) == NULL )
		if( ( pszNext = strchr( szSrch, '\t' ) ) == NULL )
		if( ( pszNext = strchr( szSrch, '\r' ) ) == NULL )
		if( ( pszNext = strchr( szSrch, '\n' ) ) == NULL )
			continue;

		if( ( pszNext - szSrch ) == strlen( pszKeyword ) && strncmp( pszKeyword, szSrch, pszNext - szSrch ) == 0 && pszNext - szSrch > 0 )
	  {
	  	while( isspace( *pszNext ) && ( pszNext - szSrch ) < strlen( szSrch ) - 1 )
	  		pszNext++;
	  	if( *pszNext == '\'' || *pszNext == '\"' )
  		{
  			pszValue = pszNext + 1;
  			if( ( pszEnd = strchr( pszValue, '\'' ) ) == NULL )
					pszEnd = strchr( pszValue, '\"' );
			}
			else
			{
				pszValue = pszNext;
				if( ( pszEnd = strchr( pszValue, ' ' ) ) == NULL )
				if( ( pszEnd = strchr( pszValue, '\t' ) ) == NULL )
				if( ( pszEnd = strchr( pszValue, '\r' ) ) == NULL )
					pszEnd = strchr( pszValue, '\n' );
			}

			if( pszEnd != NULL )
			{
				memcpy( pszOutValue, pszValue, pszEnd - pszValue);
			}
			break;
		}
	}
	fclose( fpCFG );
	return S_OK;
}

SCODE WriteCFGFile( const char *pszCFGFile, const char *pszKeyword, const char *pszInValue )
{
	FILE *fpCFG;
	FILE *fpTmpCFG;
	char szCFGFile[128];
	char szSrch[256];
	char *pszNext = NULL;
	char *pszValue = NULL;
	char *pszEnd = NULL;

	fpCFG = fopen( pszCFGFile, "r" );
	if( fpCFG == NULL )
	{
		printf( "Fail to open CFG_file:%s\n", pszCFGFile );
		syslog( LOG_ALERT, "Fail to open CFG_file:%s", pszCFGFile );
		return S_FAIL;
	}
	sprintf( szCFGFile, "%s~", pszCFGFile );
	fpTmpCFG = fopen( szCFGFile, "w" );
	if( fpTmpCFG == NULL )
	{
		printf( "Fail to open CFG_file:%s\n", szCFGFile );
		syslog( LOG_ALERT, "Fail to open CFG_file:%s", szCFGFile );
		return S_FAIL;
	}

	while( fgets( szSrch, 256, fpCFG ) != NULL )
	{
		fprintf( fpTmpCFG, "%s", szSrch );
		if( ( pszNext = strchr( szSrch, '=' ) ) != NULL )
		{
			*pszNext=' ';
		}
		if( ( pszNext = strchr( szSrch, ' ' ) ) == NULL )
			if( ( pszNext = strchr( szSrch, '\t' ) ) == NULL )
				if( ( pszNext = strchr( szSrch, '\r' ) ) == NULL )
					if( ( pszNext = strchr( szSrch, '\n' ) ) == NULL )
						continue;
		if( ( ( pszNext - szSrch ) == strlen( pszKeyword ) ) &&
				( strncmp( pszKeyword, szSrch, pszNext - szSrch ) == 0 ) &&
				( ( pszNext - szSrch ) > 0 ) )
	  {
	  	while( isspace( *pszNext ) && ( pszNext - szSrch ) < strlen(szSrch) - 1 )
	  	{
	  		pszNext++;
	  	}
	  	if( *pszNext == '\'' || *pszNext == '\"' )
  		{
  			pszValue = pszNext + 1;
  			if( ( pszEnd = strchr( pszValue, '\'' ) ) == NULL )
  			{
					pszEnd = strchr( pszValue, '\"' );
				}
			}
			else
			{
				pszValue = pszNext;
				if( ( pszEnd = strchr( pszValue, ' ' ) ) == NULL )
					if( ( pszEnd = strchr( pszValue, '\t' ) ) == NULL )
						if( ( pszEnd = strchr( pszValue, '\r' ) ) == NULL )
							pszEnd = strchr( pszValue, '\n' );
			}

			if( pszEnd != NULL )
			{
				fseek( fpTmpCFG, -strlen( szSrch ) + ( pszValue - szSrch ), SEEK_CUR);
				fprintf( fpTmpCFG, "%s", pszInValue );
				fprintf( fpTmpCFG, "%s", pszEnd );
			}
		}
	}
	ftruncate( fileno(fpTmpCFG), ftell(fpTmpCFG) );
	fclose( fpCFG );
	fclose( fpTmpCFG );
	if( rename( szCFGFile, pszCFGFile ) == -1 )
	{
		printf( "Rename %s failed: %s\n", pszCFGFile, strerror(errno) );
		return S_FAIL;
	}
	return S_OK;
}

void WriteXMLFile_SAXOpenTag(HANDLE hInstance, const char *pszTagName, const int iLen)
{
	int i;
	g_OutputFormat.iDepth++;
	g_OutputFormat.iInValue=1;
	if( ( g_OutputFormat.iMatch == ( g_OutputFormat.iDepth - 1 ) ) && ( g_OutputFormat.pszXPath != NULL ) && ( strncmp( g_OutputFormat.pszXPath, pszTagName, iLen ) == 0 ) )
	{
		if( *( g_OutputFormat.pszXPath + iLen ) == '_' )
		{
			g_OutputFormat.pszXPath += iLen + 1;
			g_OutputFormat.iMatch++;
		}
		else if( *( g_OutputFormat.pszXPath + iLen ) == '\0' )
		{
			g_OutputFormat.pszXPath = NULL;
			g_OutputFormat.iMatch++;
		}
	}
	if( g_OutputFormat.iMatch > g_OutputFormat.iDepth )
	{
		g_OutputFormat.pszXPath = NULL;
		g_OutputFormat.iMatch = 0;
	}

	for( i = 0; i < g_OutputFormat.iDepth - 1; i++ )
	{
		fputc( '	', g_OutputFormat.fpXML );
	}
	fputc( '<', g_OutputFormat.fpXML );
	fwrite( pszTagName, iLen, 1, g_OutputFormat.fpXML );
	fprintf( g_OutputFormat.fpXML, ">\n" );
}

void WriteXMLFile_SAXAttributeValue(HANDLE hInstance, const char *pszTagName, const int iTagNameLen, const char *pszAttrName, const int iAttrNameLen,	const char *pszAttrValue, const int iAttrValueLen)
{
	fseek( g_OutputFormat.fpXML, -2, SEEK_CUR);
	fputc( '	', g_OutputFormat.fpXML );
	fwrite( pszAttrName, iAttrNameLen, 1, g_OutputFormat.fpXML );
	fprintf( g_OutputFormat.fpXML, "=\"" );
	fwrite( pszAttrValue, iAttrValueLen, 1, g_OutputFormat.fpXML );
	fprintf( g_OutputFormat.fpXML, "\">\n" );
}

void WriteXMLFile_SAXCloseTag(HANDLE hInstance, const char *pszTagName, const int iLen)
{
	int i;
	if( g_OutputFormat.iInValue == 0 )
	{
		for( i = 0; i < g_OutputFormat.iDepth - 1; i++ )
		{
			fputc( '	', g_OutputFormat.fpXML );
		}
	}
	else if( g_OutputFormat.iInValue == 1 )
	{
		fseek( g_OutputFormat.fpXML, -1, SEEK_CUR);
	}
	fprintf( g_OutputFormat.fpXML, "</" );
	fwrite( pszTagName, iLen, 1, g_OutputFormat.fpXML );
	fprintf( g_OutputFormat.fpXML, ">\n" );
	g_OutputFormat.iDepth--;
	g_OutputFormat.iInValue=0;
}
void WriteXMLFile_SAXTagValue(HANDLE hInstance, const char *pszTagName, const int iTagNameLen, const char *pszTagValue, const int iTagValueLen)
{
	fseek( g_OutputFormat.fpXML, -1, SEEK_CUR);
	if( g_OutputFormat.iMatch == g_OutputFormat.iDepth )
	{
		fprintf( g_OutputFormat.fpXML, "%s", g_OutputFormat.pszValue );
		g_OutputFormat.iMatch = 0;
	}
	else
	{
		fwrite( pszTagValue, iTagValueLen, 1, g_OutputFormat.fpXML );
	}
	g_OutputFormat.iInValue = 2;
}

SCODE WriteXMLFile( const char *pszXMLFile, const char *pszXPath, const char *pszValue )
{
	char szXMLFile[128];
	TSXMLParserOptions sxmlpo;
	HANDLE hSXMLParser = NULL;
	BOOL bBoostMode    = TRUE; //Enable BoostMode by default

	memset( &g_OutputFormat, 0, sizeof( g_OutputFormat ) );
	g_OutputFormat.pszXPath = pszXPath;
	g_OutputFormat.pszValue = pszValue;

	(bBoostMode) ? sprintf( szXMLFile, "/tmp/config_temp.xml") : sprintf( szXMLFile, "%s~", pszXMLFile );

	g_OutputFormat.fpXML = fopen( szXMLFile, "w" );
	if( g_OutputFormat.fpXML == NULL )
	{
		printf( "Open %s failed: %s\n", szXMLFile, strerror(errno) );
		return S_FAIL;
	}

	memset( &sxmlpo, 0, sizeof( sxmlpo ) );
	sxmlpo.dwFlags = sxofSimpleCb | sxofSAXMode;
	sxmlpo.sxSAXMode = sxsmSimple;
	sxmlpo.hSimpleCbInstance = NULL;
	sxmlpo.pfnOpenTag = WriteXMLFile_SAXOpenTag;
	sxmlpo.pfnCloseTag = WriteXMLFile_SAXCloseTag;
	sxmlpo.pfnAttributeValue = WriteXMLFile_SAXAttributeValue;
	sxmlpo.pfnTagValue = WriteXMLFile_SAXTagValue;
	SXMLParser_Initial( &hSXMLParser );
	SXMLParser_SetOptions( hSXMLParser, &sxmlpo );
	SXMLParser_ProcessFile( hSXMLParser, pszXMLFile, sxpmSAX );
	SXMLParser_Release( &hSXMLParser, sxpmSAX );
	fclose(g_OutputFormat.fpXML);


	if (bBoostMode)
	{
		if( copy( szXMLFile, "/mnt/flash/config_tmp.xml") == -1 )
		{
			printf( "Copy %s failed\n", pszXMLFile);
			return S_FAIL;
		}
		unlink(szXMLFile);

		if( rename( "/mnt/flash/config_tmp.xml", pszXMLFile ) == -1 )
		{
			printf( "Rename %s failed: %s\n", pszXMLFile, strerror(errno) );
			return S_FAIL;
		}
	}
	else
	{
		if( rename( szXMLFile, pszXMLFile ) == -1 )
		{
			printf( "Rename %s failed: %s\n", pszXMLFile, strerror(errno) );
			return S_FAIL;
		}
	}

	return S_OK;
}

void ProcessCDF()
{
	const TXMLElement *pElement;
	const TXMLElement *pParentElement;
	const TXMLElement *pXPathElement;
	char *pszXPath = NULL;
	char szXPath[MAX_XPATH_LENGTH];
	char szCFGFile[128];
	char szValue[VALUESIZE];
	int iTagLen = 0;
	TCDFParam CDFParam;
	FILE *fpPipe;
	HANDLE hSXMLParser = NULL;
	char tmp[1024]; 

	SXMLParser_Initial( &hSXMLParser );
	memset( &szCFGFile, 0, sizeof( szCFGFile ) );
	pElement = SXMLParser_GetElementByXPath( g_hSXMLParserCDF, "root" );
	do
	{
		if( pElement->pChild != NULL )
		{
			pElement = pElement->pChild;
		}
		else if( pElement->pSibling != NULL )
		{
			pElement = pElement->pSibling;
		}
		else
		{
			while( pElement->pParent != NULL )
			{
				pElement = pElement->pParent;
				if( pElement->pSibling != NULL )
				{
					pElement = pElement->pSibling;
					break;
				}
			}
		}
		if( strncmp( pElement->pszTagName, "value", 6 ) == 0 )
		{
			memset( &szXPath, 0, sizeof( szXPath ) );
			pszXPath = szXPath + sizeof( szXPath ) - 1;
			pParentElement = pElement;
			while( ( pParentElement = pParentElement->pParent ) != NULL )
			{
				iTagLen = strlen( pParentElement->pszTagName );
				pszXPath -= iTagLen;
				memcpy( pszXPath, pParentElement->pszTagName, iTagLen );
				*(--pszXPath) = '_';
				//printf("taglen=%d, tagname=%s\n", iTagLen, pParentElement->pszTagName);
			}
			pszXPath++;
			memset( &CDFParam, 0, sizeof( CDFParam ) );
			GetCDFParam( (TXMLElement *)pElement, &CDFParam );
			if( CDFParam.pszSecLevel == NULL )
			{
				printf( "%s hasn't seclevel\n", pszXPath );
			}

			if( ( CDFParam.pszGet == NULL ) && ( CDFParam.pszCFGFile != NULL ) )
			{
				sprintf(tmp, "%s%s", g_pszPrefixETCPath, CDFParam.pszCFGFile);
				printf("%s\n", tmp);
				CDFParam.pszCFGFile = tmp;
				/*printf("%s\n", CDFParam.pszCFGFile);*/

				memset( CDFParam.pszValue, 0, VALUESIZE );
				//printf( "cfgfile=%s\n", CDFParam.pszCFGFile );
			  if( strncmp( CDFParam.pszCFGFile + strlen( CDFParam.pszCFGFile ) - 4 , ".xml", 5 ) == 0 )
			  {
			  	if( ( CDFParam.pszCFGFile != NULL ) && ( strcmp( szCFGFile, CDFParam.pszCFGFile ) != 0 ) )
			  	{
			  		printf( "SXMLParser_ProcessFile %s\n", CDFParam.pszCFGFile );
			  		if( SXMLParser_ProcessFile( hSXMLParser, CDFParam.pszCFGFile, sxpmDOM ) != S_OK )
			  		{
			  			printf( "SXMLParser_ProcessFile() is fail\n" );
			  			continue;
			  		}
			  		sprintf( szCFGFile, "%s~", CDFParam.pszCFGFile );
			  		remove( szCFGFile );
			  		strcpy( szCFGFile, CDFParam.pszCFGFile );
			  	}
			  	pXPathElement = SXMLParser_GetElementByXPath( hSXMLParser, pszXPath );
			  	if( pXPathElement != NULL )
			  	{
			  		strcpy( CDFParam.pszValue, pXPathElement->pszTagValue );
			  	}
				}
				else if( CDFParam.pszKeyword != NULL )
				{
					ReadCFGFile( CDFParam.pszCFGFile, CDFParam.pszKeyword, CDFParam.pszValue );
				}
				else
				{
					// printf( "cfgfile=%s\n", CDFParam.pszCFGFile );
					ReplaceTagName((TXMLElement *) pElement, "cfgfile", "getonce");
				}
				// else
				// {
					// memset( &szValue, 0, sizeof( szValue ) );
					// fpPipe = popen( CDFParam.pszCFGFile, "r" );
					// fgets( szValue, VALUESIZE - 1, fpPipe );
					// pclose( fpPipe );
					// if( isspace( szValue[ strlen( szValue ) - 1 ] ) )
					// {
						// szValue[ strlen( szValue ) - 1 ] = '\0';
					// }
					// strcpy( CDFParam.pszValue, szValue );
				// }
			}
			//printf( "%s=%s\n", pszXPath, CDFParam.pszValue );
		}
		//printf("Tag=%s\n", pElement->pszTagName);
	}
	while( pElement->pParent != NULL );
	printf("-------------------in ProcessCDF()-------------------\n");
	SXMLParser_Release( &hSXMLParser, sxpmDOM );
}

void GetCmd()
{
	char szXPath[MAX_XPATH_LENGTH];
	char szValue[VALUESIZE];
	char *pszTagName = NULL;
	int iPrivilege;
	const TXMLElement *pElement;
	const TXMLElement *pPreElement = NULL;
	TCDFParam CDFParam;
	FILE *fpPipe;


	pElement = SXMLParser_GetElementByXPath( g_hSXMLParserCDF, "root" );
	memset( szXPath, 0, sizeof( szXPath ) );
	strcpy( szXPath, "root" );
	memset( g_szOutBuf, 0, sizeof( g_szOutBuf ) );
	g_iOutBufLen = 0;
	OutputData( "root", StartTagType );

	do
	{
		if( pElement->pChild != NULL )
		{
			pElement = pElement->pChild;
			pszTagName = strrchr( szXPath, '\0' );
			*pszTagName = '_';
			strcpy( pszTagName + 1, pElement->pszTagName );
			if( CheckXPath( szXPath ) < 0 )
			{
				while( pElement->pSibling != NULL )
				{
					pElement = pElement->pSibling;
					pszTagName = strrchr( szXPath, '_' );
					strcpy( pszTagName + 1, pElement->pszTagName );
					if( CheckXPath( szXPath ) >= 0 )
					{
						break;
					}

					if( pElement->pSibling == NULL )
					{
						while( pElement->pParent != NULL )
						{
							pElement = pElement->pParent;
							pszTagName = strrchr( szXPath, '_' );
							*pszTagName = '\0';
							OutputData( pElement->pszTagName, EndTagType );
							if( pElement->pSibling != NULL )
							{
								break;
							}
						}
					}
				}
			}
		}
		else if( pElement->pSibling != NULL )
		{
			pElement = pElement->pSibling;
			pszTagName = strrchr( szXPath, '_' );
			strcpy( pszTagName + 1, pElement->pszTagName );
			if( CheckXPath( szXPath ) < 0 )
			{
				while( pElement->pSibling != NULL )
				{
					pElement = pElement->pSibling;
					pszTagName = strrchr( szXPath, '_' );
					strcpy( pszTagName + 1, pElement->pszTagName );
					if( CheckXPath( szXPath ) >= 0 )
					{
						break;
					}

					if( pElement->pSibling == NULL )
					{
						while( pElement->pParent != NULL )
						{
							pElement = pElement->pParent;
							pszTagName = strrchr( szXPath, '_' );
							*pszTagName = '\0';
							OutputData( pElement->pszTagName, EndTagType );
							if( pElement->pSibling != NULL )
							{
								break;
							}
						}
					}
				}
			}
		}
		else
		{
			while( ( pElement->pParent != NULL ) || ( pElement->pSibling != NULL ) )
			{
				if( pElement->pSibling != NULL )
				{
					pElement = pElement->pSibling;
					pszTagName = strrchr( szXPath, '_' );
					strcpy( pszTagName + 1, pElement->pszTagName );
					if( CheckXPath( szXPath ) >= 0 )
					{
						break;
					}
				}
				else if( pElement->pParent != NULL )
				{
					pElement = pElement->pParent;
					pszTagName = strrchr( szXPath, '_' );
					*pszTagName = '\0';
					OutputData( pElement->pszTagName, EndTagType );
				}
			}
		}

		if( pElement->pChild != NULL && pElement->pParent != NULL)
		{
			OutputData( pElement->pszTagName, StartTagType );
		}

		if( strncmp( pElement->pszTagName, "aliasxpath", 11 ) == 0 )
		{
			char szRealXPath[MAX_XPATH_LENGTH];
			memset( szRealXPath, 0, sizeof( szRealXPath ) );
			sprintf( szRealXPath, "root_%s_value", pElement->pszTagValue );
			printf( "%s -> %s\n", szXPath, szRealXPath );
			pPreElement = pElement;
			pElement = SXMLParser_GetElementByXPath( g_hSXMLParserCDF, szRealXPath );
			if( pElement == NULL )
			{
				pElement = pPreElement;
				pPreElement = NULL;
			}
		}

		if( strncmp( pElement->pszTagName, "value", 6 ) == 0 )
		{
			memset( &CDFParam, 0, sizeof( CDFParam ) );
			GetCDFParam( (TXMLElement *)pElement, &CDFParam );
			iPrivilege = 0;
			if( CDFParam.pszSecLevel != NULL )
			{
				sscanf( CDFParam.pszSecLevel, "%d", &iPrivilege );
			}
			//printf( "cmd privilege: %d, parameter privilege: %d\n", g_Cmd.iPrivilege, iPrivilege );

			pszTagName = strrchr( szXPath, '_' );
			*pszTagName = '\0';
			OutputData( szXPath + 5, XPathType );
			*pszTagName = '_';

			if( g_Cmd.iPrivilege < iPrivilege )
			{
				OutputData( "ERR_SECURITY", ValueType );
			}
			else if( ( g_Cmd.iBuf == 0 ) && ( CDFParam.pszGet != NULL ) && ( strcmp( CDFParam.pszGet, "none") != 0 ) )
			{
				// printf( "get=%s\n", CDFParam.pszGet );
				memset( &szValue, 0, sizeof( szValue ) );
				fpPipe = popen( CDFParam.pszGet, "r" );
				fgets( szValue, VALUESIZE - 1, fpPipe );
				pclose( fpPipe );
				if( isspace( szValue[ strlen( szValue ) - 1 ] ) )
				{
					szValue[ strlen( szValue ) - 1 ] = '\0';
				}
				OutputData( szValue, ValueType );
			}
			else if( CDFParam.pszGetOnce != NULL )
			{
				printf( "getonce=%s\n", CDFParam.pszGetOnce );
				memset( &szValue, 0, sizeof( szValue ) );
				fpPipe = popen( CDFParam.pszGetOnce, "r" );
				fgets( szValue, VALUESIZE - 1, fpPipe );
				pclose( fpPipe );
				if( isspace( szValue[ strlen( szValue ) - 1 ] ) )
				{
					szValue[ strlen( szValue ) - 1 ] = '\0';
				}
				OutputData( szValue, ValueType );
				strcpy( CDFParam.pszValue, szValue );
				//Only once
				ReplaceTagName((TXMLElement *) pElement, "getonce", "cfgfile");
			}
			else if( CDFParam.pszValue != NULL )
			{
				OutputData( CDFParam.pszValue, ValueType );
			}
		}

		if( pPreElement != NULL )
		{
			pElement = pPreElement;
			pPreElement = NULL;
		}
		//printf("Tag=%s\n", pElement->pszTagName);
	}
	while( pElement->pParent != NULL );

	//printf( "%s\n", g_szOutBuf );
}

void AddProcess( const char *pszProcess, int iPriority )
{
	int i;
	int iInsertIdx = 0;

	for( i = 0; i < g_Process.iNum; i++ )
	{
		if( strcmp( g_Process.szValue[ i ], pszProcess ) == 0 )
		{
			return;
		}
		if( iPriority >= g_Process.iPriority[ i ] )
		{
			iInsertIdx = i + 1;
		}
	}
	pthread_mutex_lock( &pmutexSignalProcess );
	for( i = g_Process.iNum - 1; i >= iInsertIdx; i-- )
	{
		g_Process.iPriority[ i + 1 ] = g_Process.iPriority[ i ];
		strcpy( g_Process.szValue[ i + 1 ], g_Process.szValue[ i ] );
	}
	g_Process.iPriority[ iInsertIdx ] = iPriority;
	strcpy( g_Process.szValue[ iInsertIdx ], pszProcess );
	g_Process.iNum++;
	pthread_mutex_unlock( &pmutexSignalProcess );

	for( i = 0; i < g_Process.iNum; i++ )
	{
		printf( "index: %d, process: %s, priority: %d\n", i, g_Process.szValue[ i ], g_Process.iPriority[ i ] );
	}
}

void GenerateCmd( char *pszOutCmd, const char *pszInCmd, const char *pszValue )
{
	char szCmd[512];
	char szXPath[MAX_XPATH_LENGTH];
	char szEscapedValue[ 2 * VALUESIZE + 1 ];
	char *pszStart;
	char *pszEnd;
	char* pcNew;
	const char *pszPos = pszInCmd;
	const char* pcOld;
	const TXMLElement *pElement;

	memset( szCmd, 0, sizeof( szCmd ) );
	while( ( ( pszStart = strstr( pszPos, "${" ) ) != 0 ) && ( ( pszEnd = strstr( pszPos, "}" ) ) != 0 ) )
	{
		memcpy( szCmd + strlen( szCmd ), pszPos, pszStart - pszPos );
		memset( szXPath, 0, sizeof( szXPath ) );
		pszStart += 2;
		memcpy( szXPath, "root_", 5 );
		memcpy( 5 + szXPath, pszStart, pszEnd - pszStart );
		memcpy( 5 + szXPath + ( pszEnd - pszStart ), "_value", 6 );
		pElement = SXMLParser_GetElementByXPath( g_hSXMLParserCDF, szXPath );
		if( ( pElement != NULL ) && ( pElement->pszTagValue != NULL ) )
		{
			pcOld = pElement->pszTagValue;
			pcNew = szEscapedValue;
			while( *pcOld != '\0' )
			{
				if( *pcOld != '$' )
				{
					*pcNew = *pcOld;
				}
				else
				{
					// Insert '\' before '$' character to escape shell variable replacement
					*pcNew = '\\';
					pcNew++;
					*pcNew = *pcOld;
				}
				pcNew++;
				pcOld++;
			}
			*pcNew = '\0';
			sprintf( szCmd + strlen( szCmd ), "%s",  szEscapedValue );
		}
		pszPos = pszEnd + 1;
	}
	sprintf( szCmd + strlen( szCmd ), "%s", pszPos );

	pcOld = pszValue;
	pcNew = szEscapedValue;
	while( *pcOld != '\0' )
	{
		if( *pcOld != '$' )
		{
			*pcNew = *pcOld;
		}
		else
		{
			// Insert '\' before '$' character to escape shell variable replacement
			*pcNew = '\\';
			pcNew++;
			*pcNew = *pcOld;
		}
		pcNew++;
		pcOld++;
	}
	*pcNew = '\0';
	sprintf( pszOutCmd, szCmd, szEscapedValue );
	printf( "OutCmd=%s\nInCmd=%s\nValue=%s\n", pszOutCmd, pszInCmd, pszValue );
}

void SetCmd()
{
	char szXPath[MAX_XPATH_LENGTH];
	char szParamXPath[MAX_XPATH_LENGTH];
	char szRealXPath[MAX_XPATH_LENGTH];
	char *pszTagName = NULL;
	int iCmdIdx = -1;
	int iPrivilege;
	const TXMLElement *pElement;
	const TXMLElement *pPreElement = NULL;
	TCDFParam CDFParam;

	pElement = SXMLParser_GetElementByXPath( g_hSXMLParserCDF, "root" );
	memset( szXPath, 0, sizeof( szXPath ) );
	strcpy( szXPath, "root" );
	memset( g_szOutBuf, 0, sizeof( g_szOutBuf ) );
	g_iOutBufLen = 0;
	OutputData( "root", StartTagType );
	g_Message.iNum = 0;
	memset( g_Process.iPriority, 0, sizeof( g_Process.iPriority ) );

	do
	{
		if( pElement->pChild != NULL )
		{
			pElement = pElement->pChild;
			pszTagName = strrchr( szXPath, '\0' );
			*pszTagName = '_';
			strcpy( pszTagName + 1, pElement->pszTagName );
			if( ( iCmdIdx = CheckXPath( szXPath ) ) < 0 )
			{
				while( pElement->pSibling != NULL )
				{
					pElement = pElement->pSibling;
					pszTagName = strrchr( szXPath, '_' );
					strcpy( pszTagName + 1, pElement->pszTagName );
					if( ( iCmdIdx = CheckXPath( szXPath ) ) >= 0 )
					{
						break;
					}

					if( pElement->pSibling == NULL )
					{
						while( pElement->pParent != NULL )
						{
							pElement = pElement->pParent;
							pszTagName = strrchr( szXPath, '_' );
							*pszTagName = '\0';
							OutputData( pElement->pszTagName, EndTagType );
							if( pElement->pSibling != NULL )
							{
								break;
							}
						}
					}
				}
			}
		}
		else if( pElement->pSibling != NULL )
		{
			pElement = pElement->pSibling;
			pszTagName = strrchr( szXPath, '_' );
			strcpy( pszTagName + 1, pElement->pszTagName );
			if( ( iCmdIdx = CheckXPath( szXPath ) ) < 0 )
			{
				while( pElement->pSibling != NULL )
				{
					pElement = pElement->pSibling;
					pszTagName = strrchr( szXPath, '_' );
					strcpy( pszTagName + 1, pElement->pszTagName );
					if( ( iCmdIdx = CheckXPath( szXPath ) ) >= 0 )
					{
						break;
					}

					if( pElement->pSibling == NULL )
					{
						while( pElement->pParent != NULL )
						{
							pElement = pElement->pParent;
							pszTagName = strrchr( szXPath, '_' );
							*pszTagName = '\0';
							OutputData( pElement->pszTagName, EndTagType );
							if( pElement->pSibling != NULL )
							{
								break;
							}
						}
					}
				}
			}
		}
		else
		{
			while( ( pElement->pParent != NULL ) || ( pElement->pSibling != NULL ) )
			{
				if( pElement->pSibling != NULL )
				{
					pElement = pElement->pSibling;
					pszTagName = strrchr( szXPath, '_' );
					strcpy( pszTagName + 1, pElement->pszTagName );
					if( ( iCmdIdx = CheckXPath( szXPath ) ) >= 0 )
					{
						break;
					}
				}
				else if( pElement->pParent != NULL )
				{
					pElement = pElement->pParent;
					pszTagName = strrchr( szXPath, '_' );
					*pszTagName = '\0';
					OutputData( pElement->pszTagName, EndTagType );
				}
			}
		}

		if( pElement->pChild != NULL && pElement->pParent != NULL)
		{
			OutputData( pElement->pszTagName, StartTagType );
		}

		if( strncmp( pElement->pszTagName, "aliasxpath", 11 ) == 0 )
		{
			memset( szRealXPath, 0, sizeof( szRealXPath ) );
			sprintf( szRealXPath, "root_%s_value", pElement->pszTagValue );
			printf( "%s -> %s\n", szXPath, szRealXPath );
			pPreElement = pElement;
			pElement = SXMLParser_GetElementByXPath( g_hSXMLParserCDF, szRealXPath );
			if( pElement == NULL )
			{
				pElement = pPreElement;
				pPreElement = NULL;
			}
			pszTagName = strrchr( szRealXPath, '_' );
			*pszTagName = '\0';
		}

		if( strncmp( pElement->pszTagName, "value", 6 ) == 0 )
		{
			memset( &CDFParam, 0, sizeof( CDFParam ) );
			GetCDFParam( (TXMLElement *)pElement, &CDFParam );

			pszTagName = strrchr( szXPath, '_' );
			*pszTagName = '\0';
			OutputData( szXPath + 5, XPathType );
			memset( szParamXPath, 0, sizeof( szParamXPath ) );
			if( pPreElement != NULL )
			{
				pElement = pPreElement;
				pPreElement = NULL;
				strcpy( szParamXPath, szRealXPath );
			}
			else
			{
				strcpy( szParamXPath, szXPath );
			}
			*pszTagName = '_';

			iPrivilege = 0;
			if( CDFParam.pszSecLevel != NULL )
			{
				sscanf( strchr( CDFParam.pszSecLevel, '/') + 1, "%d", &iPrivilege );
			}
			//printf( "cmd privilege: %d, parameter privilege: %d\n", g_Cmd.iPrivilege, iPrivilege );

			if( g_Cmd.iPrivilege < iPrivilege )
			{
				OutputData( "ERR_SECURITY", ValueType );
			}
			else if( ( ( g_Cmd.pszValue[iCmdIdx] != NULL ) && ( CDFParam.pszValue != NULL ) && ( strcmp( g_Cmd.pszValue[iCmdIdx], CDFParam.pszValue ) != 0 ) ) || ( CDFParam.pszSet != NULL ) )
			{
				if( ( g_Cmd.iCheck == 1 ) && ( CDFParam.pszCheck != NULL ) &&
						( g_Cmd.pszValue[iCmdIdx][0] != '\0' || CDFParam.pszCheck[0] == '!' ) &&
						( CheckValue( CDFParam.pszCheck, g_Cmd.pszValue[iCmdIdx] ) != S_OK ) )
				{
					OutputData( "ERR_INVALID", ValueType );
					continue;
				}
				memset( CDFParam.pszValue, 0, VALUESIZE );
				strcpy( CDFParam.pszValue, g_Cmd.pszValue[iCmdIdx] );
				OutputData( CDFParam.pszValue, ValueType );

				if( g_Cmd.iBuf == 0 )
				{
					if( g_Cmd.iOption & CMD_OPT_PROCESS )
					{
						char szProcess[1024];
						if( CDFParam.pszProcess != NULL )
						{
							if( ( CDFParam.pszProcess != NULL ) && ( strcmp( CDFParam.pszProcess, "none" ) == 0 ) )
							{
								printf( "none process\n" );
							}
							else if( CDFParam.pszProcess[0] != '+' )
							{
								GenerateCmd( szProcess, CDFParam.pszProcess, CDFParam.pszValue );
								AddProcess( szProcess, iCmdIdx );
							}
							else
							{
								GenerateCmd( szProcess, CDFParam.pszProcess + 1, CDFParam.pszValue );
								AddProcess( szProcess, iCmdIdx );
								if( ( CDFParam.pszParentProcess != NULL ) && ( strcmp( CDFParam.pszParentProcess, "none" ) != 0 ) )
								{
									GenerateCmd( szProcess, CDFParam.pszParentProcess, CDFParam.pszValue );
									AddProcess( szProcess, iCmdIdx );
								}
							}
						}
						else if( ( CDFParam.pszParentProcess != NULL ) && ( strcmp( CDFParam.pszParentProcess, "none" ) != 0 ) )
						{
							GenerateCmd( szProcess, CDFParam.pszParentProcess, CDFParam.pszValue );
							AddProcess( szProcess, iCmdIdx );
						}
					}

					if( ( g_Cmd.iOption & CMD_OPT_SIGNAL ) && ( CDFParam.pszPidFile != NULL ) && ( strcmp( CDFParam.pszPidFile, "none" ) !=0 ) && ( CDFParam.pszSig != NULL ) )
					{
						int i;
						pthread_mutex_lock( &pmutexSignalProcess );
						strcpy( g_Sig.szPidFile[ g_Sig.iNum ], CDFParam.pszPidFile );
						strcpy( g_Sig.szValue[ g_Sig.iNum ], CDFParam.pszSig );
						g_Sig.iNum++;
						for( i=0; i < g_Sig.iNum - 1; i++ )
						{
							if( ( strcmp( g_Sig.szPidFile[ i ], CDFParam.pszPidFile ) == 0 ) &&
									( strcmp( g_Sig.szValue[ i ], CDFParam.pszSig ) == 0 ) )
							{
								g_Sig.iNum--;
								break;
							}
						}
						pthread_mutex_unlock( &pmutexSignalProcess );
					}

					if( ( g_Cmd.iOption & CMD_OPT_MESSAGE ) && ( CDFParam.pszMsgKey != NULL ) && ( strcmp( CDFParam.pszMsgKey, "none" ) !=0 ) )
					{
						int iMsgId;
						int i;
						char *pcType;
						char *pszValue;
						WORD *pwTag;
						WORD *pwLength;
						key_t keyMsg;
						TMsg Msg;

						keyMsg = (key_t) atoi( CDFParam.pszMsgKey );
						if( keyMsg > 0 )
						{
							iMsgId = msgget( keyMsg, 0666 | IPC_CREAT );
							if( iMsgId == -1)
							{
								printf( "msgget failed with error: %d\n", errno );
							}
							else
							{
								pwTag = (WORD *)Msg.szData;
								pwLength = (WORD *)(Msg.szData + 2);
								pszValue = Msg.szData + 4;
								memset( &Msg, 0, sizeof( Msg ) );
								pcType = strchr( CDFParam.pszMsgKey, ':');
								if( pcType != NULL )
								{
									Msg.msg_type = atoi( pcType + 1 );
								}
								*pwTag = MSG_TAG_NAMEVALUE;
								*pwLength = sprintf( pszValue, "%s=%s", szParamXPath + 5, CDFParam.pszValue );
								printf( "Send %d bytes message \"%s\" to msgkey %d, type %d\n", *pwLength, pszValue, keyMsg, (int)Msg.msg_type );
								if( msgsnd( iMsgId, (void *) &Msg, sizeof( Msg.szData ), IPC_NOWAIT ) == -1)
								{
									printf( "%s\n", strerror(errno) );
								}
								for(i=0; i < g_Message.iNum; i++)
								{
									if(g_Message.iId[i] == iMsgId && g_Message.iType[i] == Msg.msg_type)
									{
										break;
									}
								}
								if( i == g_Message.iNum )
								{
									g_Message.iId[g_Message.iNum] = iMsgId;
									g_Message.iType[g_Message.iNum] = Msg.msg_type;
									g_Message.iNum++;
								}
							}
						}
					}

					if( CDFParam.pszSet != NULL )
					{
						char szSet[1024];
						GenerateCmd( szSet, CDFParam.pszSet, CDFParam.pszValue );
						printf( "system(%s)\n", szSet );
						pthread_mutex_lock( &pmutexSystem );
						system( szSet );
						pthread_mutex_unlock( &pmutexSystem );
					}
					else if( CDFParam.pszCFGFile != NULL )
					{
						if( strncmp( CDFParam.pszCFGFile + strlen( CDFParam.pszCFGFile ) - 4 , ".xml", 5 ) == 0 )
						{
							WriteXMLFile( CDFParam.pszCFGFile, szParamXPath, CDFParam.pszValue );
						}
						else if( CDFParam.pszKeyword != NULL )
						{
							//printf( "write %s to %s of %s\n", CDFParam.pszValue, CDFParam.pszKeyword, CDFParam.pszCFGFile );
							WriteCFGFile( CDFParam.pszCFGFile, CDFParam.pszKeyword, CDFParam.pszValue );
						}
					}
				}
			}
			else
			{
				OutputData( g_Cmd.pszValue[iCmdIdx], ValueType );
			}
			//printf("Tag=%s\n", pElement->pszTagName);
		}
	}
	while( pElement->pParent != NULL );

	//Send End Tage to Message Queues
	{
		int i;
		WORD *pwTag;
		TMsg Msg;
		for( i = 0; i < g_Message.iNum; i++ )
		{
			pwTag = (WORD *)Msg.szData;
			memset( &Msg, 0, sizeof( Msg ) );
			Msg.msg_type = g_Message.iType[i];
			*pwTag = MSG_TAG_END;
			if( msgsnd( g_Message.iId[i], (void *) &Msg, sizeof( Msg.szData ), IPC_NOWAIT ) == -1)
			{
				printf( "%s\n", strerror(errno) );
			}
		}
		g_Message.iNum = 0;
	}
}

SCODE ApplyCmd()
{
	int iPrivilege;
	int iCmdIdx = 1;
	char szXPath[MAX_XPATH_LENGTH];
	char szRealXPath[MAX_XPATH_LENGTH];
	char cNULL = '\0';
	char *pszTagName = NULL;
	const char *pszValue = NULL;
	HANDLE hSXMLParser = NULL;
	const TXMLElement *pElement;
	const TXMLElement *pElementCDF = NULL;
	TCDFParam CDFParam;

	SXMLParser_Initial( &hSXMLParser );
	if( SXMLParser_ProcessFile( hSXMLParser, g_Cmd.szCFGFile, sxpmDOM ) != S_OK )
	{
		SXMLParser_Release( &hSXMLParser, sxpmDOM );
		return S_FAIL;
	}

	pElement = SXMLParser_GetElementByXPath( hSXMLParser, "root" );
	memset( szXPath, 0, sizeof( szXPath ) );
	strcpy( szXPath, "root" );
	memset( g_szOutBuf, 0, sizeof( g_szOutBuf ) );
	g_iOutBufLen = 0;
	OutputData( "root", StartTagType );
	g_Message.iNum = 0;
	memset( g_Process.iPriority, 0, sizeof( g_Process.iPriority ) );

	do
	{
		if( pElement->pChild != NULL )
		{
			pElement = pElement->pChild;
			pszTagName = strrchr( szXPath, '\0' );
			*pszTagName = '_';
			strcpy( pszTagName + 1, pElement->pszTagName );
			if( CheckXPath( szXPath ) < 0 )
			{
				while( pElement->pSibling != NULL )
				{
					pElement = pElement->pSibling;
					pszTagName = strrchr( szXPath, '_' );
					strcpy( pszTagName + 1, pElement->pszTagName );
					if( CheckXPath( szXPath ) >= 0 )
					{
						break;
					}

					if( pElement->pSibling == NULL )
					{
						while( pElement->pParent != NULL )
						{
							pElement = pElement->pParent;
							pszTagName = strrchr( szXPath, '_' );
							*pszTagName = '\0';
							OutputData( pElement->pszTagName, EndTagType );
							if( pElement->pSibling != NULL )
							{
								break;
							}
						}
					}
				}
			}
		}
		else if( pElement->pSibling != NULL )
		{
			pElement = pElement->pSibling;
			pszTagName = strrchr( szXPath, '_' );
			strcpy( pszTagName + 1, pElement->pszTagName );
			if( CheckXPath( szXPath ) < 0 )
			{
				while( pElement->pSibling != NULL )
				{
					pElement = pElement->pSibling;
					pszTagName = strrchr( szXPath, '_' );
					strcpy( pszTagName + 1, pElement->pszTagName );
					if( CheckXPath( szXPath ) >= 0 )
					{
						break;
					}

					if( pElement->pSibling == NULL )
					{
						while( pElement->pParent != NULL )
						{
							pElement = pElement->pParent;
							pszTagName = strrchr( szXPath, '_' );
							*pszTagName = '\0';
							OutputData( pElement->pszTagName, EndTagType );
							if( pElement->pSibling != NULL )
							{
								break;
							}
						}
					}
				}
			}
		}
		else
		{
			while( ( pElement->pParent != NULL ) || ( pElement->pSibling != NULL ) )
			{
				if( pElement->pSibling != NULL )
				{
					pElement = pElement->pSibling;
					pszTagName = strrchr( szXPath, '_' );
					strcpy( pszTagName + 1, pElement->pszTagName );
					if( CheckXPath( szXPath ) >= 0 )
					{
						break;
					}
				}
				else if( pElement->pParent != NULL )
				{
					pElement = pElement->pParent;
					pszTagName = strrchr( szXPath, '_' );
					*pszTagName = '\0';
					OutputData( pElement->pszTagName, EndTagType );
				}
			}
		}

		OutputData( pElement->pszTagName, StartTagType );
		if( pElement->pChild == NULL )
		{
			if( pElement->pszTagValue == NULL )
			{
				pszValue = &cNULL;
				printf( "NULL value\n" );
			}
			else
			{
				pszValue = pElement->pszTagValue;
			}
			memset( szRealXPath, 0, sizeof( szRealXPath ) );
			sprintf( szRealXPath, "%s_value", szXPath );
			pElementCDF = SXMLParser_GetElementByXPath( g_hSXMLParserCDF, szRealXPath );
			if( pElementCDF == NULL )
			{
				memset( szRealXPath, 0, sizeof( szRealXPath ) );
				sprintf( szRealXPath, "%s_aliasxpath", szXPath );
				pElementCDF = SXMLParser_GetElementByXPath( g_hSXMLParserCDF, szRealXPath );
				if( pElementCDF != NULL )
				{
					memset( szRealXPath, 0, sizeof( szRealXPath ) );
					sprintf( szRealXPath, "root_%s_value", pElementCDF->pszTagValue );
					printf( "%s -> %s\n", szXPath, szRealXPath );
					pElementCDF = SXMLParser_GetElementByXPath( g_hSXMLParserCDF, szRealXPath );
				}
			}
			pszTagName = strrchr( szRealXPath, '_' );
			*pszTagName = '\0';
			OutputData( szXPath + 5, XPathType );

			if( pElementCDF != NULL )
			{
				memset( &CDFParam, 0, sizeof( CDFParam ) );
				GetCDFParam( (TXMLElement *)pElementCDF, &CDFParam );
				iPrivilege = 0;
				if( CDFParam.pszSecLevel != NULL )
				{
					sscanf( strchr( CDFParam.pszSecLevel, '/') + 1, "%d", &iPrivilege );
				}
				//printf( "cmd privilege: %d, parameter privilege: %d\n", g_Cmd.iPrivilege, iPrivilege );

				if( g_Cmd.iPrivilege < iPrivilege )
				{
					OutputData( "ERR_SECURITY", ValueType );
				}
				else if( ( ( strcmp( pszValue, CDFParam.pszValue ) != 0 ) || ( CDFParam.pszSet != NULL ) ) && ( strcmp( pszValue, "ERR_SECURITY" ) != 0 ) )
				{
					if( ( g_Cmd.iCheck == 1 ) && ( CDFParam.pszCheck != NULL ) &&
							( pszValue[0] != '\0' || CDFParam.pszCheck[0] == '!' ) &&
							( CheckValue( CDFParam.pszCheck, pszValue ) != S_OK ) )
					{
						OutputData( "ERR_INVALID", ValueType );
						continue;
					}

					memset( CDFParam.pszValue, 0, VALUESIZE );
					strcpy( CDFParam.pszValue, pszValue );
					OutputData( CDFParam.pszValue, ValueType );

					if( g_Cmd.iBuf == 0 )
					{
						if( g_Cmd.iOption & CMD_OPT_PROCESS )
						{
							char szProcess[1024];
							if( CDFParam.pszProcess != NULL )
							{
								if( ( CDFParam.pszProcess != NULL ) && ( strcmp( CDFParam.pszProcess, "none" ) == 0 ) )
								{
									printf( "none process\n" );
								}
								else if( CDFParam.pszProcess[0] != '+' )
								{
									GenerateCmd( szProcess, CDFParam.pszProcess, CDFParam.pszValue );
									AddProcess( szProcess, iCmdIdx++ );
								}
								else
								{
									GenerateCmd( szProcess, CDFParam.pszProcess + 1, CDFParam.pszValue );
									AddProcess( szProcess, iCmdIdx++ );
									if( ( CDFParam.pszParentProcess != NULL ) && ( strcmp( CDFParam.pszParentProcess, "none" ) != 0 ) )
									{
										GenerateCmd( szProcess, CDFParam.pszParentProcess, CDFParam.pszValue );
										AddProcess( szProcess, iCmdIdx++ );
									}
								}
							}
							else if( ( CDFParam.pszParentProcess != NULL ) && ( strcmp( CDFParam.pszParentProcess, "none" ) != 0 ) )
							{
								GenerateCmd( szProcess, CDFParam.pszParentProcess, CDFParam.pszValue );
								AddProcess( szProcess, iCmdIdx++ );
							}
						}

						if( ( g_Cmd.iOption & CMD_OPT_SIGNAL ) && ( CDFParam.pszPidFile != NULL ) && ( strcmp( CDFParam.pszPidFile, "none" ) !=0 ) && ( CDFParam.pszSig != NULL ) )
						{
							int i;
							pthread_mutex_lock( &pmutexSignalProcess );
							strcpy( g_Sig.szPidFile[ g_Sig.iNum ], CDFParam.pszPidFile );
							strcpy( g_Sig.szValue[ g_Sig.iNum ], CDFParam.pszSig );
							g_Sig.iNum++;
							for( i=0; i < g_Sig.iNum - 1; i++ )
							{
								if( ( strcmp( g_Sig.szPidFile[ i ], CDFParam.pszPidFile ) == 0 ) &&
										( strcmp( g_Sig.szValue[ i ], CDFParam.pszSig ) == 0 ) )
								{
									g_Sig.iNum--;
									break;
								}
							}
							pthread_mutex_unlock( &pmutexSignalProcess );
						}

						if( ( g_Cmd.iOption & CMD_OPT_MESSAGE ) && ( CDFParam.pszMsgKey != NULL ) && ( strcmp( CDFParam.pszMsgKey, "none" ) !=0 ) )
						{
							int iMsgId;
							int i;
							char *pcType;
							char *pszValue;
							WORD *pwTag;
							WORD *pwLength;
							key_t keyMsg;
							TMsg Msg;

							keyMsg = (key_t) atoi( CDFParam.pszMsgKey );
							if( keyMsg > 0 )
							{
								iMsgId = msgget( keyMsg, 0666 | IPC_CREAT );
								if( iMsgId == -1)
								{
									printf( "msgget failed with error: %d\n", errno );
								}
								else
								{
									pwTag = (WORD *)Msg.szData;
									pwLength = (WORD *)(Msg.szData + 2);
									pszValue = Msg.szData + 4;
									memset( &Msg, 0, sizeof( Msg ) );
									pcType = strchr( CDFParam.pszMsgKey, ':');
									if( pcType != NULL )
									{
										Msg.msg_type = atoi( pcType + 1 );
									}
									*pwTag = MSG_TAG_NAMEVALUE;
									*pwLength = sprintf( pszValue, "%s=%s", szRealXPath + 5, CDFParam.pszValue );
									printf( "Send %d bytes message \"%s\" to msgkey %d, type %d\n", *pwLength, pszValue, keyMsg, (int)Msg.msg_type );
									if( msgsnd( iMsgId, (void *) &Msg, sizeof( Msg.szData ), IPC_NOWAIT ) == -1)
									{
										printf( "%s\n", strerror(errno) );
									}
									for(i=0; i < g_Message.iNum; i++)
									{
										if(g_Message.iId[i] == iMsgId && g_Message.iType[i] == Msg.msg_type)
										{
											break;
										}
									}
									if( i == g_Message.iNum )
									{
										g_Message.iId[g_Message.iNum] = iMsgId;
										g_Message.iType[g_Message.iNum] = Msg.msg_type;
										g_Message.iNum++;
									}
								}
							}
						}

						if( CDFParam.pszSet != NULL )
						{
							char szEscapedSetValue[ 2 * VALUESIZE + 1 ];
							char* pcOld = CDFParam.pszValue;
							char* pcNew = szEscapedSetValue;
							char szSet[256];

							while( *pcOld != '\0' )
							{
								if( *pcOld != '$' )
								{
									*pcNew = *pcOld;
								}
								else
								{
									// Insert '\' before '$' character to escape shell variable replacement
									*pcNew = '\\';
									pcNew++;
									*pcNew = *pcOld;
								}
								pcNew++;
								pcOld++;
							}
							*pcNew = '\0';
							sprintf( szSet, CDFParam.pszSet, szEscapedSetValue );
							printf( "system(%s)\n", szSet );
							pthread_mutex_lock( &pmutexSystem );
							system( szSet );
							pthread_mutex_unlock( &pmutexSystem );
						}
						else if( CDFParam.pszCFGFile != NULL )
						{
							if( strncmp( CDFParam.pszCFGFile + strlen( CDFParam.pszCFGFile ) - 4 , ".xml", 5 ) == 0 )
							{
								WriteXMLFile( CDFParam.pszCFGFile, szRealXPath, CDFParam.pszValue );
							}
							else if( CDFParam.pszKeyword != NULL )
							{
								//printf( "write %s to %s of %s\n", CDFParam.pszValue, CDFParam.pszKeyword, CDFParam.pszCFGFile );
								WriteCFGFile( CDFParam.pszCFGFile, CDFParam.pszKeyword, CDFParam.pszValue );
							}
						}
					}
				}
				else
				{
					OutputData( pszValue, ValueType );
				}
			}
			else
			{
				OutputData( "ERR_XPATH", ValueType );
			}
		}
	}
	while( pElement->pParent != NULL );
	SXMLParser_Release( &hSXMLParser, sxpmDOM );

	//Send End Tage to Message Queues
	{
		int i;
		WORD *pwTag;
		TMsg Msg;
		for( i = 0; i < g_Message.iNum; i++ )
		{
			pwTag = (WORD *)Msg.szData;
			memset( &Msg, 0, sizeof( Msg ) );
			Msg.msg_type = g_Message.iType[i];
			*pwTag = MSG_TAG_END;
			if( msgsnd( g_Message.iId[i], (void *) &Msg, sizeof( Msg.szData ), IPC_NOWAIT ) == -1)
			{
				printf( "%s\n", strerror(errno) );
			}
		}
		g_Message.iNum = 0;
	}
	return S_OK;
}

/* ==================================================================== */
void Configer_SignalHandler(int iSigNo)
{
        if ( (iSigNo == SIGTERM) || (iSigNo == SIGINT) )
        {
                printf("Receive TERM/INT signal!\n");
                g_bTerminated = TRUE;
        }
        else if (iSigNo == SIGPIPE)
        {
                printf("Receive SIGPIPE!\n");
        }

        return;
}

/* ==================================================================== */
void Configer_InitSignal()
{
        struct sigaction tSigAct;

        // For program termination signal
        tSigAct.sa_handler = Configer_SignalHandler;
        sigemptyset(&tSigAct.sa_mask);
        tSigAct.sa_flags = SA_RESTART;
        sigaction(SIGTERM, &tSigAct, NULL);
        sigaction(SIGINT, &tSigAct, NULL);
        sigaction(SIGPIPE, &tSigAct, NULL);

        return;
}


int main( int argc, char *argv[] )
{
	char *pszFileCDF = NULL;
	char *pszDirCDF = NULL;
	char *pszCDF = NULL;
	char *pszEndCDF = NULL;
	char szFullPath[256];
	char szCmdBuf[8192];
	int iOption;
	int	iFDSck;
	int iFDClient;
	int iClientLen;
	int iCDFSize = 0;
	int iCDFLen = 0;
	int iSemId;
	int iRet;
	struct dirent *dirEntry;
	struct sockaddr_un Client;
	FILE *fpCDF;
	DIR *dirPool;
	pthread_t pthreadSignalProcess;
	TSXMLParserOptions sxmlpo;
	union semun semunConfiger;
	key_t keyConfiger;
	struct sembuf sb = {0, -MAX_SEMAPHORE_VAL, 0};
	SCODE scResult;
	//20101123 Added by danny For support advanced system log
	char *pszSrch;
	const char *pcSetParamLevel = NULL;
	char szCwd[1024];

	if (getcwd(szCwd, sizeof(szCwd)) != NULL)
	{
		V_CALL_CHKNEQ_EX( ftok( szCwd, 'c' ), keyConfiger, -1, return 1; );
		/*fprintf(stdout, "Current working dir: %s\n", szCwd);*/
		/*fprintf(stdout, "KeyConfiger: %x\n", keyConfiger);*/
	}
	else
	{
		keyConfiger = 0x123456;
		perror("getcwd() error");
	}

	while((iOption = getopt(argc, argv, "dhvi:f:m:e:")) != -1) {
		switch (iOption) {
		case 'i':
			pszFileCDF = optarg;
			break;
		case 'f':
			pszDirCDF = optarg;
			break;
		case 'd':
			daemon(0, 0);
			break;
		case 'v':
			ShowVersion();
			break;
		case 'e':
			g_pszPrefixETCPath = optarg;
			break;
		case 'h':
		default:
			Usage();
		}
	}
	if( pszFileCDF == NULL )
	{
		Usage();
	}

	Configer_InitSignal();
	openlog("[CONFIGER]", LOG_NDELAY, LOG_USER);
	/*V_CALL_CHKNEQ_EX( ftok( "/usr/sbin/configer", 'c' ), keyConfiger, -1, return 1; );*/
	V_CALL_CHKNEQ_EX( semget( keyConfiger, 1, 0666 | IPC_CREAT ), iSemId, -1, return 1; );
	memset( &semunConfiger, 0, sizeof( semunConfiger ) );
	semunConfiger.val = MAX_SEMAPHORE_VAL;
	V_CALL_CHKNEQ_EX( semctl( iSemId, 0, SETVAL, semunConfiger ), iRet, -1, return 1; );

	signal( SIGPIPE,SIG_IGN );
	V_CALL_CHKNEQ_EX( CreateUnixSocket( SOCKETPATH ), iFDSck, -1, return 1; );
	listen( iFDSck, 5 );
	memset( &g_Sig, 0, sizeof( g_Sig ) );
	memset( &g_Process, 0, sizeof( g_Process ) );

	V_CALL_CHKNEQ_EX( fopen( pszFileCDF, "r" ), fpCDF, NULL, return 1; );
	fseek( fpCDF, 0, SEEK_END );
	iCDFSize = ftell( fpCDF );
	fclose( fpCDF );
	if( pszDirCDF != NULL )
	{
		V_CALL_CHKNEQ_EX( opendir( pszDirCDF ), dirPool, NULL, return 1; );
		while( dirEntry = readdir ( dirPool ) )
		{
			if( ( strcmp ( dirEntry->d_name, "." ) == 0) || ( strcmp (dirEntry->d_name, "..") == 0))
			{
				continue;
			}
			snprintf( szFullPath, sizeof( szFullPath ) - 1, "%s/%s", pszDirCDF, dirEntry->d_name );
			printf( "Find %s\n", szFullPath );
			V_CALL_CHKNEQ_EX( fopen( szFullPath, "r" ), fpCDF, NULL, return 1; );
			fseek( fpCDF, 0, SEEK_END );
			iCDFSize += ftell( fpCDF );
			fclose( fpCDF );
		}
		closedir(dirPool);
	}
	printf( "CDF size is %d bytes\n", iCDFSize );
	pszCDF = malloc( iCDFSize );

	V_CALL_CHKNEQ_EX( fopen( pszFileCDF, "r" ), fpCDF, NULL, return 1; );
	iCDFLen = fread( pszCDF, 1, iCDFSize, fpCDF );
	fclose( fpCDF );
	if( pszDirCDF != NULL )
	{
		V_CALL_CHKNEQ_EX( opendir( pszDirCDF ), dirPool, NULL, return 1; );
		pszEndCDF = strstr( pszCDF, "</root>" );
		iCDFLen = ( int ) ( pszEndCDF - pszCDF );
		while( dirEntry = readdir( dirPool ) )
		{
			if( ( strcmp( dirEntry->d_name, "." ) == 0 ) || ( strcmp( dirEntry->d_name, ".." ) == 0 ) )
			{
				continue;
			}
			snprintf( szFullPath, sizeof( szFullPath ) - 1, "%s/%s", pszDirCDF, dirEntry->d_name );
			V_CALL_CHKNEQ_EX( fopen( szFullPath, "r" ), fpCDF, NULL, return 1; );
			iCDFLen += fread( pszCDF + iCDFLen, 1, iCDFSize - iCDFLen, fpCDF );
			fclose(fpCDF);
		}
		closedir(dirPool);
		iCDFLen += sprintf( pszCDF + iCDFLen, "</root>" );
	}
	//printf( "%s", pszCDF );
	SXMLParser_Initial( &g_hSXMLParserCDF );
	memset( &sxmlpo, 0, sizeof( sxmlpo ) );
	sxmlpo.dwFlags = sxofDOMshmKey;
	sxmlpo.keyShm = keyConfiger;
	SXMLParser_SetOptions( g_hSXMLParserCDF, &sxmlpo );
	SXMLParser_Process( g_hSXMLParserCDF, pszCDF, sxpmDOMshm );
	free(pszCDF);
	ProcessCDF();
	SetModifyTime();
	Swatchdog_Message_Compose_KickWatchDog();
	pthread_mutex_init( &pmutexSignalProcess, NULL );
	pthread_mutex_init( &pmutexSystem, NULL );
	pthread_create( &pthreadSignalProcess, NULL, SendSignalAndRunProcess, NULL );

	//20101123 Added by danny For support advanced system log
	if( IsAdvLogSupport() )
	{
		pcSetParamLevel = SXMLParser_GetTagValueByXPath(g_hSXMLParserCDF, SYSLOG_SETPARAM_XPATH);
	}

	Swatchdog_StartWatchMe();

	do
	{
		iClientLen = sizeof( Client );
		g_iClientConnect = 0;
		iFDClient = accept( iFDSck, (struct sockaddr *)&Client, &iClientLen );
		g_iClientConnect = 1;
		memset( szCmdBuf, 0, sizeof( szCmdBuf ) );
		read( iFDClient, szCmdBuf, sizeof( szCmdBuf ) - 1 );

		/* parse cmd from unix socket */
		/*printf( "cmd=%s\n", szCmdBuf );*/
		if( ParseCmd( szCmdBuf ) != S_OK )
		{
//			write( iFDClient, "error cmd", 9 );
			close( iFDClient );
			continue;
		}

		if( strcmp( g_Cmd.szMethod, "get" ) == 0 )
		{
			GetCmd();
		}
		else if( strcmp( g_Cmd.szMethod, "set" ) == 0 )
		{
			printf( "get semaphore\n" );

			//20101123 Added by danny For support advanced system log
			if( ( pcSetParamLevel != NULL ) && ( strncmp( pcSetParamLevel, "0", sizeof(char) ) != 0 ) && ( strncmp( pcSetParamLevel, "1", sizeof(char) ) != 0 ) )
			{
				pszSrch = strchr( szCmdBuf, '\n' );
				if( pszSrch != NULL )
				{
					pszSrch += 1;
					openlog("[CONFIGER]",0, LOG_LOCAL1);
					syslog( LOG_INFO, "Set %s", pszSrch );
					openlog("[CONFIGER]",0, LOG_USER);
				}
			}

			sb.sem_op = -MAX_SEMAPHORE_VAL;
			V_CALL_CHKNEQ_EX( semop( iSemId, &sb, 1 ), iRet, -1, perror("semop"); );
			SetCmd();
			sb.sem_op = MAX_SEMAPHORE_VAL;
			V_CALL_CHKNEQ_EX( semop( iSemId, &sb, 1 ), iRet, -1, perror("semop"); );
			printf( "release semaphore\n" );
		}
		else if( strcmp( g_Cmd.szMethod, "apply" ) == 0 )
		{
			printf( "get semaphore\n" );
			sb.sem_op = -MAX_SEMAPHORE_VAL;
			V_CALL_CHKNEQ_EX( semop( iSemId, &sb, 1 ), iRet, -1, perror("semop"); );
			scResult = ApplyCmd();
			sb.sem_op = MAX_SEMAPHORE_VAL;
			V_CALL_CHKNEQ_EX( semop( iSemId, &sb, 1 ), iRet, -1, perror("semop"); );
			printf( "release semaphore\n" );
			if( scResult != S_OK )
			{
				write( iFDClient, "fail to open XML_file", 21 );
				close( iFDClient );
				continue;
			}
		}

		if( g_iOutBufLen != 0 )
		{
			write( iFDClient, g_szOutBuf, g_iOutBufLen );
		}
		else
		{
			write( iFDClient, "error operation", 15 );
		}
		close( iFDClient );
	}
	while(!g_bTerminated);
	close( iFDSck );
	if (unlink( SOCKETPATH ) != 0)
	{
	       perror("unlink");
	}
	pthread_mutex_destroy( &pmutexSignalProcess );
	pthread_mutex_destroy( &pmutexSystem );
	SXMLParser_Release( &g_hSXMLParserCDF, sxpmDOMshm );
	if (semctl(iSemId, 0, IPC_RMID, 0) == -1) 
	{
	       perror("semctl: IPC_RMID");
	}
	syslog( LOG_ALERT, "Process exit" );
	return 0;
}

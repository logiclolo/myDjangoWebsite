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
 * conflib.c
 *
 * \brief
 * Configer library
 *
 * \date
 * 2009/09/21
 *
 * \author
 * Ben Chen
 *
 *******************************************************************************
 */
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <fcntl.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/msg.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/shm.h>
#include <sys/ipc.h>
#include <sys/sem.h>
#include <errno.h>
#include <sys/time.h>
#include <signal.h>
#include <linux/types.h>
#include "typedef.h"
#include "conflib.h"
#include "sxmlparser.h"

SCODE Configer_Control( TConfOpt *pConfopt, char *pszOutBuffer, DWORD dwSize )
{
	struct	sockaddr_un	sunx;
	int iFD;
	char szCmd[8192];
	char szBuf[1024];

	memset( szCmd, 0, sizeof( szCmd ) );
	if( ( pConfopt->szType[0] == '\0' ) || ( pConfopt->pszXPath == NULL ) )
	{
		return S_FAIL;
	}
	
	switch( pConfopt->eCmd )
	{
		case eGetCmd:
			snprintf( szCmd, sizeof( szCmd ) - 1, "get %s %d %d\n%s", pConfopt->szType, pConfopt->iPrivilege, pConfopt->iBuffer, pConfopt->pszXPath );
			break;
		case eSetCmd:
			snprintf( szCmd, sizeof( szCmd ) - 1, "set %s %d %d %d\n%s", pConfopt->szType, pConfopt->iPrivilege, pConfopt->iCheck, pConfopt->iBuffer, pConfopt->pszXPath );
			break;
		case eApplyCmd:
			if( pConfopt->szCFGFile[0] == '\0' )
			{
				return S_FAIL;
			}
			snprintf( szCmd, sizeof( szCmd ) - 1, "apply %s %d %d %s\n%s", pConfopt->szType, pConfopt->iPrivilege, pConfopt->iCheck, pConfopt->szCFGFile, pConfopt->pszXPath );
			break;
		default:
			return S_FAIL;
	}
	
	//printf( "Cmd=%s\n", szCmd );
	/* Create the unix socket */
	iFD = socket( AF_UNIX, SOCK_STREAM, 0 );
	if( iFD < 0 )
	{
		printf( "cannot create socket (%d).%s\n", errno, strerror( errno ) );
		return S_FAIL;
	}
	memset( &sunx, 0, sizeof( sunx ) );
	sunx.sun_family = AF_UNIX;
	(void) strncpy( sunx.sun_path, "/tmp/configer", sizeof( sunx.sun_path ) );		
	if( connect( iFD, (struct sockaddr *)&sunx,	sizeof( sunx.sun_family ) + strlen( sunx.sun_path ) ) < 0)
	{
		printf( "connect failed!" );
		close( iFD );
		return S_FAIL;
	}
	write( iFD, szCmd, strlen( szCmd ) );
	if( pszOutBuffer == NULL )
	{
		memset( szBuf, 0, sizeof( szBuf ) );		
		while( read( iFD, szBuf, sizeof( szBuf ) - 1 ) > 0 )
		{
			printf( "%s", szBuf );
			memset( szBuf, 0, sizeof( szBuf ) );
		}
	}
	else
	{
		if( read( iFD, pszOutBuffer, dwSize ) == dwSize )
		{
			close( iFD );
			return S_FAIL;
		}
	}
	close( iFD );
	return S_OK;
}

void *MapRealAddr( TDOMshm *pTDOMshm, const void *PreAddr )
{
	void *PreBaseAddr = pTDOMshm->pBaseAddr;
	void *CurBaseAddr = pTDOMshm;
	//printf( "previous address=%p, previous base address=%p, current base address=%p\n", PreAddr, PreBaseAddr, CurBaseAddr );
	return ( PreAddr - PreBaseAddr + CurBaseAddr );
}

void GetRealElement( TDOMshm *pTDOMshm, const TXMLElement *pOrgElement, TXMLElement *pRealElement )
{
	memset( pRealElement, 0, sizeof( TXMLElement ) );
	pRealElement->iIndex = pOrgElement->iIndex;
	pRealElement->pszTagName = MapRealAddr( pTDOMshm, pOrgElement->pszTagName );
	pRealElement->pszTagValue = MapRealAddr( pTDOMshm, pOrgElement->pszTagValue );
	pRealElement->iChildCount = pOrgElement->iChildCount;
	pRealElement->iAttrCount = pOrgElement->iAttrCount;
	pRealElement->pAttribute = MapRealAddr( pTDOMshm, pOrgElement->pAttribute );
	pRealElement->pChild = MapRealAddr( pTDOMshm, pOrgElement->pChild );
	pRealElement->pSibling = MapRealAddr( pTDOMshm, pOrgElement->pSibling );
	pRealElement->pParent = MapRealAddr( pTDOMshm, pOrgElement->pParent );
}

const TXMLElement *GetElementByXPath( TDOMshm *pTDOMshm, const char *pszXPath )
{
	int bFound = 0;
	int iTagLen = 0;
	const char *pszTagName;
	const char *pszNextTagName = pszXPath;
	const TXMLElement *pElement;
	const TXMLElement *pPrevElement = NULL;
	TXMLElement Element;
	
	pElement = MapRealAddr( pTDOMshm, pTDOMshm->pRoot );
	pElement = pElement->pChild;
	do
	{
		bFound = 0;
		pszTagName = pszNextTagName;
		for( ; *pszNextTagName != '_' && *pszNextTagName != 0; pszNextTagName++ );
		iTagLen = pszNextTagName - pszTagName;
		while( pElement )
		{
			pElement = MapRealAddr( pTDOMshm, pElement );
			GetRealElement( pTDOMshm, pElement, &Element );
			if( ( strlen( Element.pszTagName ) == iTagLen ) && ( strncmp( Element.pszTagName, pszTagName, iTagLen ) == 0 ) )
			{
				pPrevElement = pElement;
				pElement = pElement->pChild;
				bFound = 1;
				break;
			}
			pElement = pElement->pSibling;
		}
		if( !bFound )
		{
			return NULL;
		}
	}
	while( (*pszNextTagName++) != 0 );
	
	return pPrevElement;
}

BOOL IfGetOnce(TDOMshm *pTDOMshm, const TXMLElement *pElement)
{
	TXMLElement Element;
	if( pElement->pParent != NULL )
	{
		pElement = MapRealAddr( pTDOMshm, pElement->pParent );
		pElement = pElement->pChild; 
	}

	while( pElement )
	{
		pElement = MapRealAddr( pTDOMshm, pElement );
		GetRealElement( pTDOMshm, pElement, &Element );
		// printf("pElement->pszTagName = %p %s\n", Element.pszTagName, Element.pszTagName);
		if( strncmp( Element.pszTagName, "getonce", 8 ) == 0 )
		{
			return TRUE;
		}
		pElement = pElement->pSibling;
	}
	return FALSE;
}

SCODE Configer_GetParamValueByXPath( const char *pszXPath, char *pszValue, DWORD dwSize )
{
	int iShmId;
	int iSemId;
	const TXMLElement *pElement;
	TXMLElement Element;
	TDOMshm *pTDOMshm;
	key_t keyConfiger;
	BOOL bIsCFGFile = FALSE;
	struct sembuf sb = {0, -1, SEM_UNDO};
	char szCwd[1024];
	
	/*
	if( ( keyConfiger = ftok( "/usr/sbin/configer", 'c' ) ) == -1 )
	{
		perror("ftok");
		return S_FAIL;
	}
	*/
	if (getcwd(szCwd, sizeof(szCwd)) != NULL)
	{
		/*V_CALL_CHKNEQ_EX( ftok( szCwd, 'c' ), keyConfiger, -1, return 1; );*/
		keyConfiger = ftok( szCwd, 'c');
		/*fprintf(stdout, "Current working dir: %s\n", szCwd);*/
		/*fprintf(stdout, "KeyConfiger: %x\n", keyConfiger);*/
	}
	else
	{
		keyConfiger = 0x123456;
		perror("getcwd() error");
	}
	if( ( iSemId = semget( keyConfiger, 1, 0 ) ) == -1 )
	{
		perror("semget");
		return S_FAIL;
	}
	
	if( semop( iSemId, &sb, 1 ) == -1 )
	{
		perror("semop");
		return S_FAIL;
	}
	sb.sem_op = 1;
	
	iShmId = shmget( keyConfiger, 0, 0 );	
	pTDOMshm = shmat( iShmId, (void *)0, 0 );
	//printf( "Base address = %p, root element address = %p\n", pTDOMshm->pBaseAddr, pTDOMshm->pRoot );
	
	pElement = GetElementByXPath( pTDOMshm, pszXPath );
	if( pElement != NULL )
	{
		pElement = pElement->pChild;
	}
	
	while( pElement )
	{		
		pElement = MapRealAddr( pTDOMshm, pElement );
		GetRealElement( pTDOMshm, pElement, &Element );
		if( ( strlen( Element.pszTagName ) == 5 ) && ( strncmp( Element.pszTagName, "value", 5 ) == 0 ) )
		{
			SCODE scRet = S_FAIL;

			strncpy( pszValue, Element.pszTagValue, dwSize );
			if ( (*Element.pszTagValue == '\0') && IfGetOnce(pTDOMshm, pElement))
			{
				bIsCFGFile = TRUE;
				break;
			}

			if( semop( iSemId, &sb, 1 ) == -1 )
			{
				perror("semop");
				scRet = S_FAIL;
			}
			else
			{
				if( strlen( Element.pszTagValue ) < dwSize )
				{
					scRet = S_OK;
				}
				else
				{
					scRet = S_FAIL;
				}
			}
			shmdt( pTDOMshm );
			return scRet;
		}
		else if( ( strlen( Element.pszTagName ) == 10 ) && ( strncmp( Element.pszTagName, "aliasxpath", 10 ) == 0 ) )
		{
			pElement = GetElementByXPath( pTDOMshm, Element.pszTagValue );
			if( pElement != NULL )
			{
				pElement = pElement->pChild;
			}
		}
		else
		{
			pElement = pElement->pSibling;
		}
	}
	shmdt( pTDOMshm );	
	if( semop( iSemId, &sb, 1 ) == -1 )
	{
		perror("semop");
		return S_FAIL;
	}
	
	if (bIsCFGFile)
	{
		TConfOpt tConfOpt = {
                        .eCmd = eGetCmd,
                        .szType = "Value",
                        .pszXPath = NULL,
                        .iPrivilege = 99,
                        .iCheck = 0,
                        .iBuffer = 0 };
		tConfOpt.pszXPath = (char *) pszXPath;
		return Configer_Control( &tConfOpt, pszValue, dwSize );
	}
	return S_FAIL;
}

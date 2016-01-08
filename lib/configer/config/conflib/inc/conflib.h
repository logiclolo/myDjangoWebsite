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
 * Copyright 2000-2007 Vivotek, Inc. All rights reserved.
 *
 * \file
 * conflib.h
 *
 * \brief
 * header file of configer library
 *
 * \date
 * 2009/09/21
 *
 * \author
 * Ben Chen
 *
 *******************************************************************************
 */
#ifndef	_CONF_LIB_H_
#define	_CONF_LIB_H_
#include "typedef.h"

typedef enum {
	eGetCmd,
	eSetCmd,
	eApplyCmd
} ECmd;

typedef struct {
ECmd eCmd;
char szType[16];
char szCFGFile[128];
char *pszXPath;
int iPrivilege;
int iCheck;
int iBuffer;
} TConfOpt;

SCODE Configer_Control( TConfOpt *pConfopt, char *pszOutBuffer, DWORD dwSize );
SCODE Configer_GetParamValueByXPath( const char *pszXPath, char *pszValue, DWORD dwSize );

#endif

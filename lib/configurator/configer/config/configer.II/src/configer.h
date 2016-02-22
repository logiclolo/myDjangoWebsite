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
 * configer.h
 *
 * \brief
 * the header file of configer
 *
 * \date
 * 2009/09/07
 *
 * \author
 * Ben Chen
 *
 *******************************************************************************
 */
#define _VCALL_REPORT
#define CMD_MAX_NUM 512
#define MAX_XPATH_LENGTH 256
#define LIMITED_NUM 10
#define MAX_SIGNAL_NUM 20
#define MAX_PROCESS_NUM 20
#define MAX_MESSAGE_NUM 20
#ifndef VALUESIZE
	#define VALUESIZE 300
#endif
#define MAX_SEMAPHORE_VAL 10

//20101123 Added by danny For support advanced system log
#define SYSLOG_CONF								"/etc/syslog.conf"
#define CONFIGSET_LOG							"messages_configset"
#define SYSLOG_SETPARAM_XPATH			"root_syslog_setparamlevel_value"

/* The datagram of message data
 *   __________________________________
 *  | Tag  | Length |       data       |
 *  |______|________|__________________|
 *    2Byte   2Byte
 * */
#define MSG_TAG_NAMEVALUE 0x0001
#define MSG_TAG_END 0xFFFF

typedef struct{
	long msg_type;
	char szData[512];
} TMsg;

typedef struct {
	char szPidFile[MAX_SIGNAL_NUM][128];
	char szValue[MAX_SIGNAL_NUM][VALUESIZE];
	int iNum;
} TSig;
TSig g_Sig;

typedef struct {
	char szValue[MAX_PROCESS_NUM][VALUESIZE];
	int iPriority[MAX_PROCESS_NUM];
	int iNum;
} TProcess;
TProcess g_Process;

typedef struct {
	int iId[MAX_MESSAGE_NUM];
	int iType[MAX_MESSAGE_NUM];
	int iNum;
} TMessage;
TMessage g_Message;

typedef struct {
	const char *pszCFGFile;
	const char *pszParentProcess;
	const char *pszProcess;
	const char *pszSig;
	const char *pszPidFile;
	const char *pszSecLevel;
	const char *pszGet;
	const char *pszGetOnce;
	const char *pszSet;
	const char *pszCheck;
	const char *pszKeyword;
	const char *pszAliasXPath;
	const char *pszMsgKey;
	char *pszValue;
} TCDFParam;

#define CMD_OPTION "cmdopt="
#define CMD_OPT_PROCESS 0x1
#define CMD_OPT_SIGNAL 0x2
#define CMD_OPT_MESSAGE 0x4

typedef struct {
	int iOption;
	int iCheck;
	int iBuf;
	int iPrivilege;
	int iNum;
	char szMethod[10];
	char szType[20];
	char szCFGFile[128];
	char szXPath[8192];
	char *pszXPath[CMD_MAX_NUM];
	char *pszValue[CMD_MAX_NUM];
} TCmd;
TCmd g_Cmd;

typedef enum {
	StartTagType,
	EndTagType,
	XPathType,
	ValueType,
} EOutputType;

typedef struct {
	int iDepth;
	int iInValue;
	int iMatch;
	const char *pszXPath;
	const char *pszValue;
	FILE *fpXML;
} TOutputFormat;
TOutputFormat g_OutputFormat;

typedef enum {
	eCheckByNumber,
	eCheckByStringLength,
	eCheckByEnumerate,
	eCheckByMultiple,
	eCheckByRegularExpression
} ECheckRules;

union semun {
	int val;              /* used for SETVAL only */
	struct semid_ds *buf; /* for IPC_STAT and IPC_SET */
	ushort *array;        /* used for GETALL and SETALL */
};

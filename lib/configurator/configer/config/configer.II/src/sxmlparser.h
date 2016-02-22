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
 * sxmlparser.h
 *
 * \brief
 * A simple, small and standalone XML parser
 *
 * \date
 * 2009/08/06
 *
 * \author
 * Joe Wu
 *
 *******************************************************************************
 */

#ifndef _S_XMLPARSER_H_
#define _S_XMLPARSER_H_

#include "typedef.h"

#define SXMLPARSER_VERSION	MAKEFOURCC(1,0,0,1)

//! error code for SXML parser module
#define errSXMLStateError			(SCODE)(0x80001000)
#define errXMLTagUnbalance			(SCODE)(0x80000010)		//!< open/close tag unbalance
#define errXMLMissingStartOfTag		(SCODE)(0x8000000F)		//!< missing start of tag
#define errSXMLMissingQuote			(SCODE)(0x8000000E)		//!< missing quote for attribute value
#define errSXMLMissingEndOfTag 		(SCODE)(0x8000000D)		//!< missing end of tag
#define errSXMLMissingCloseHeader 	(SCODE)(0x8000000C)		//!< missing close header
#define errSXMLMissingCloseComment 	(SCODE)(0x8000000B)		//!< missing close comment
#define errSXMLPushError			(SCODE)(0x8000000A)		
#define errSXMLNULLAttrValue		(SCODE)(0x80000009)		//!< the attribute value is NULL
//#define errSXMLNULLAttrName			(SCODE)(0x80000008)		//!< the attribute name is NULL
//#define errSXMLNULLTagValue			(SCODE)(0x80000007)		//!< the tag value is NULL
#define errSXMLNULLTagName			(SCODE)(0x80000006)		//!< the tag name is NULL
#define errSXMLMissingCloseTag 		(SCODE)(0x80000005)		//!< missing close tags
#define	errSXMLOutOfMemory 			(SCODE)(0x80000004)		//!< out of memory
#define	errSXMLInternalError 		(SCODE)(0x80000003)		//!< internal library error
#define	errSXMLInvalidSettings		(SCODE)(0x80000002)		//!< invalid settings
#define	errSXMLFailed 				(SCODE)(0x80000001)		//!< Generic error

//! flags for SXML option settings
typedef enum {
	sxofSAXMode				= 0x01,	//!< Select SAX mode
	sxofSimpleCb			= 0x02,	//!< Set SAX simple mode callback function
	sxofPatternMatchData	= 0x04,	//!< set SAX pattern match data structure
	sxofDOMshmKey	= 0x08,	//!< set DOM shared memory key
} ESXMLParserOptionFlags;

//! XML processing mode
typedef enum {
	sxpmDOM = 1,	//!< DOM mode
	sxpmSAX = 2,	//!< SAX mode
	sxpmDOMshm = 3	//!< DOM mode in shared memory
} ESXMLProcessMode;

//! SAX mode
typedef enum {
	sxsmSimple			= 1,	//!< simple callback mode
	sxsmPatternMatch	= 2		//!< pattern match mode
} ESXMLSAXMode;

//! attribute structure of XML 
typedef struct _tXMLAttribute {
	int			iIndex;
	const char	*pszName;
	const char	*pszValue;
} TXMLAttribute;

//! element structure of XML
typedef struct _tXMLElement {
	int					iIndex;
	const char			*pszTagName;
	const char			*pszTagValue;
	int					iChildCount;
	int					iAttrCount;
	TXMLAttribute		*pAttribute;	//!< pointer to attribute list
	struct _tXMLElement *pChild;		//!< start of child
	struct _tXMLElement *pSibling;		//!< next sibling
	struct _tXMLElement *pParent;		//!< parent
} TXMLElement;

// callbacks for tags, attributes in SAX simple mode
typedef void (* PFSXMLParser_OpenTag)(HANDLE hInstance, const char *pszTagName, const int iLen);
typedef void (* PFSXMLParser_CloseTag)(HANDLE hInstance, const char *pszTagName, const int iLen);
typedef void (* PFSXMLParser_AttributeValue)(HANDLE hInstance, 
											 const char *pszTagName, const int iTagNameLen,
											 const char *pszAttrName, const int iAttrNameLen,
											 const char *pszAttrValue, const int iAttrValueLen);

typedef void (* PFSXMLParser_TagValue)(HANDLE hInstance, const char *pszTagName, const int iTagNameLen,
														 const char *pszTagValue, const int iTagValueLen);

// callback function for SAX pattern match mode
typedef void (* PFSXMLParser_PatternMatch)(HANDLE hInstance, int iIndex, const char *pszValue, const int iValueLen, const char *pszWildcard, const int iWildcardLen);

// pattern definitions:
// tag.tag.tag[#attr][*]
typedef struct _tSAXPatternMatch {
	const char *pszPattern;
	PFSXMLParser_PatternMatch pfnCb;
} TSAXPatternMatch;

typedef struct tSXMLParserOptions {
	DWORD 							dwFlags;
	ESXMLSAXMode					sxSAXMode;

	// followings are parameters for simple SAX callback mode
	PFSXMLParser_OpenTag			pfnOpenTag;	
	PFSXMLParser_CloseTag			pfnCloseTag;
	PFSXMLParser_AttributeValue		pfnAttributeValue;
	PFSXMLParser_TagValue			pfnTagValue;
	HANDLE							hSimpleCbInstance;

	// followings are parameters for pattern match SAX callback mode
	TSAXPatternMatch				*pSAXPatternMatch;
	HANDLE							hPatternMatchInstance;
	key_t keyShm;
} TSXMLParserOptions;

typedef struct tDOMshm {
	void *pBaseAddr;
	struct _tXMLElement *pRoot;
} TDOMshm;

SCODE SXMLParser_Initial(HANDLE *phObject);
SCODE SXMLParser_Release(HANDLE *phObject, ESXMLProcessMode sxMode);
SCODE SXMLParser_SetOptions(HANDLE hObject, const TSXMLParserOptions *pOptions);
SCODE SXMLParser_Process(HANDLE hObject, const BYTE *pszXMLStream, ESXMLProcessMode sxMode);
SCODE SXMLParser_ProcessFile(HANDLE hObject, const char *pszFileName, ESXMLProcessMode sxMode);

// the following functions are for DOM mode processing
const TXMLElement *SXMLParser_EnumStart(HANDLE hObject);
const TXMLElement *SXMLParser_EnumNext(HANDLE hObject);

int SXMLParser_GetElementCount(HANDLE hObject);
int SXMLParser_GetAttributeCount(HANDLE hObject);

//! usage: to get root.system.hostname => SXMLParser_GetTagValueByName(hObject, "root", "system", "hostname", NULL);
const char *SXMLParser_GetTagValueByName(HANDLE hObject, ...);
//! usage: to get attribute "xmlns:xsi" of root element => SXMLParser_GetAttrValueByName(hObject, "xmlns:xsi", "root", NULL);
const char *SXMLParser_GetAttrValueByName(HANDLE hObject, ...);
const char *SXMLParser_GetTagValueByIndex(HANDLE hObject, int iIndex);
const char *SXMLParser_GetAttrValueByIndex(HANDLE hObject, int iIndex);

int SXMLParser_GetTagIndex(HANDLE hObject, ...);
int SXMLParser_GetAttrIndex(HANDLE hObject, ...);

const TXMLElement *SXMLParser_GetElementByTag(HANDLE hObject, ...);
const TXMLElement *SXMLParser_GetElementByIndex(HANDLE hObject, int iIndex);

const TXMLElement *SXMLParser_GetElementByXPath(HANDLE hObject, char *pszXPath);
const char *SXMLParser_GetTagValueByXPath(HANDLE hObject, char *pszXPath);
SCODE SXMLParser_SetTagValueByXPath(HANDLE hObject, char *pszXPath, char *TagValue);

#endif // _S_XMLPARSER_H_

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
 * sxmlparser_local.c
 *
 * \brief
 * Locally included file for simple XML parser
 *
 * \date
 * 2009/08/06
 *
 * \author
 * Joe Wu
 *
 *******************************************************************************
 */

#ifndef _SXMLPARSER_LOCAL_H_
#define _SXMLPARSER_LOCAL_H_

#include "sxmlparser.h"

//#define MAX_ATTR_COUNT_SHIFT	6

#ifndef MAX_TAG_VALUE_LEN
#define MAX_TAG_VALUE_LEN	256
#endif

/*
#ifndef MAX_NAME_LENGTH
#define MAX_NAME_LENGTH		32
#endif

#ifndef MAX_VALUE_LENGTH
#define MAX_VALUE_LENGTH	128
#endif

#ifndef MAX_XML_DEPTH
#define MAX_XML_DEPTH		8
#endif
*/

//! internal callback type 
typedef enum {
	sxcbOpenTag		= 1,
	sxcbCloseTag	= 2,
	sxcbTagValue	= 4,
	sxcbAttrName	= 8,
	sxcbAttrValue	= 16,
	sxcbComment		= 32,
	sxcbHeader		= 64,
} ESXMLCbType;

//! Internal used callback function
typedef SCODE (* PFSXMLParser_InternalCb)(HANDLE hInstance, const ESXMLCbType sxcbType, const unsigned char *pszValue, const int iLength);

typedef enum {
	STATE_START,             //  0 scanning whitespace before first <
	STATE_OPEN_TAG,          //  1 scanning the first character of the tag's name
	STATE_TAG_NAME,          //  2 scanning the tag's name
	STATE_WS,                //  3 scanning whitespace between attributes
	STATE_ATTR_NAME,         //  4 scanning the attribute's name
	STATE_WS_ATTR_EQUAL,     //  5 scanning whitepsace before =
	STATE_WS_ATTR_VALUE,     //  6 scanning whitespace between = and attribute value
	STATE_ATTR_VALUE_SINGLE, //  7 scanning the attribute's value inside single quotes
	STATE_ATTR_VALUE_DOUBLE, //  8 scanning the attribute's value inside double quotes
	STATE_CLOSE_TAG,         //  9 scanning after the / looking for >
	STATE_TAG_VALUE,         // 10 scanning text between tags
	STATE_OPEN_COMMENT,		 // 11 scanning the first character of the comment
	STATE_OPEN_HEADER,		 
} ESXMLParseStateX;


typedef enum {
	sxsWhiteSpace,
	sxsOpenTag,
	//sxsCloseTag,
	sxsAttrName,
	sxsAttrValue,
	sxsTagName,
	//sxsTagValue,
	sxsComment,
	sxsHeader
} ESXMLParseState;

typedef struct tSXMLCallback {
	PFSXMLParser_InternalCb		pfnCb;	
	HANDLE						hInstance;
} TSXMLCallback;

typedef struct tSXMLParserInfo {
	ESXMLSAXMode				sxSAXMode;

	PFSXMLParser_OpenTag		pfnOpenTag;	
	PFSXMLParser_CloseTag		pfnCloseTag;
	PFSXMLParser_AttributeValue	pfnAttributeValue;
	PFSXMLParser_TagValue		pfnTagValue;
	HANDLE						hSimpleCbInstance;

	TSAXPatternMatch			*pSAXPatternMatch;
	HANDLE						hPatternMatchInstance;

	ESXMLParseState				vxsParserState;	// parser state

	void						*pvDOMMem;
	int							iDOMMemSize;

	int							iXMLDepth;				//!< depth of XML
	int							iXMLStrSize;			//!< size of strings in XML stream
	int							iXMLElementCount;		//!< total element count
	int							iXMLAttributeCount;		//!< total attribute feild count
	unsigned char				*pszXMLString;			//!< pointer to memory to storing XML strings
	TXMLElement					*pXMLElement;			//!< pointer to XMLElement
	TXMLAttribute				*pXMLAttribute;			//!< pointer to XMLAttribute

	int							iStackPos;				//!< position of Stack
	int							iElemIndex;				//!< Index of element
	int							iAttrIndex;				//!< Index of attribute
	unsigned char				*pszCurXMLStr;			//!< current position of XML String
	TXMLElement					*pCurElement;			//1< point to current element used for construction
	TXMLElement				   **ppXMLElementStack;		//!< pointer to element stack
	TXMLAttribute				*pCurAttribute;			//!< point to current attribute element
	key_t keyShm;
} TSXMLParserInfo;

//! simple callback mode SAX internal structure
typedef struct tSAXSimpleCbInfo {
	const unsigned char *pszTagName;
	const unsigned char *pszTagValue;
	const unsigned char *pszAttrName;
	//const unsigned char *pszAttrValue;

	int iTagNameLen;
	int iTagValueLen;
	int iAttrNameLen;
	//int iAttrValueLen;

	TSXMLParserInfo *pXMLParserInfo;
} TSAXSimpleCbInfo;

//! pattern match mode SAX internal structure
typedef struct tSAXPatternMatchInfo {
	int				iPatternIndex;
	int				iStrIndex;
	int				bEndOfPattern;
	int				bIsWildcard;
	TSXMLParserInfo *pXMLParserInfo;
} TSAXPatternMatchInfo;

#define PTHIS	((TSXMLParserInfo *)hObject)

#endif

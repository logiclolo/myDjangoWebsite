#---------------------------------------------------------------------
#  $Header:$
#  Copyright (c) 2000-2007 Vivotek Inc. All rights reserved.
#
#  +-----------------------------------------------------------------+
#  | THIS SOFTWARE IS FURNISHED UNDER A LICENSE AND MAY ONLY BE USED |
#  | AND COPIED IN ACCORDANCE WITH THE TERMS AND CONDITIONS OF SUCH  |
#  | A LICENSE AND WITH THE INCLUSION OF THE THIS COPY RIGHT NOTICE. |
#  | THIS SOFTWARE OR ANY OTHER COPIES OF THIS SOFTWARE MAY NOT BE   |
#  | PROVIDED OR OTHERWISE MADE AVAILABLE TO ANY OTHER PERSON. THE   |
#  | OWNERSHIP AND TITLE OF THIS SOFTWARE IS NOT TRANSFERRED.        |
#  |                                                                 |
#  | THE INFORMATION IN THIS SOFTWARE IS SUBJECT TO CHANGE WITHOUT   |
#  | ANY PRIOR NOTICE AND SHOULD NOT BE CONSTRUED AS A COMMITMENT BY |
#  | VIVOTEK INC.                                                    |
#  +-----------------------------------------------------------------+
#
#  Project name         : NONE
#  Module name          : config.mk
#  Module description   : configuration for makefile inclusion
#  Author               : Joe Wu
#  Created at           : 2006/08/02
#  $History:$
#
#---------------------------------------------------------------------

#---------------------------------------------------------------------
# Configurations
#---------------------------------------------------------------------

# general configuration, for each configuration
#---------------------------------------------------------------------
PLATFORM 	= _LINUX
INCDIR	 	= $(PROJ_ROOT)/$(swatchdog_app)/inc
SYSDEFS  	= $(configer_sysdef)
CFLAGS	 	= 
USRDEFS  	= $(configer_usrdef)
LINKFLAGS   = -lpthread
TOOL_CONFIG = GenericLinux
MLIBS		= $(common_lib) $(message_lib)

# specific configuration
#---------------------------------------------------------------------
ifeq "$(BUILD_CONF)" "linux_release"
CFLAGS	 	= -O3 -D_NDEBUG -Wall
endif

#---------------------------------------------------------------------
ifeq "$(BUILD_CONF)" "linux_debug"
CFLAGS		= -O0 -Wall
endif

#---------------------------------------------------------------------
ifeq "$(BUILD_CONF)" "vcwin32_release"
PLATFORM 	= _WIN32_
TOOL_CONFIG = VCWin32
LIBS		= $(common)
CFLAGS	 	= /O2 -D_NDEBUG
endif

#---------------------------------------------------------------------
ifeq "$(BUILD_CONF)" "armlinux_release"
PLATFORM	= _LINUX
TOOL_CONFIG	= ARMLinux
CFLAGS	 	= -O3 -D_NDEBUG -Wall
endif

#---------------------------------------------------------------------
ifeq "$(BUILD_CONF)" "armlinux_debug"
PLATFORM	= _LINUX
TOOL_CONFIG	= ARMLinux
CFLAGS	 	= -O0 -D_DEBUG -Wall -g
endif

#---------------------------------------------------------------------
# tool settings
#---------------------------------------------------------------------

include $(MAKEINC)/tools.mk
ifeq "$(TOOL_CONFIG)" "CONFIG_NAME"
# you can add your additional tools configuration here
endif

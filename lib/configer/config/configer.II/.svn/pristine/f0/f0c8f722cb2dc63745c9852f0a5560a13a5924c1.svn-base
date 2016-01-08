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
#  Module name          : mod1_test
#  Module description   : module1 testing program
#  Author               : Joe Wu
#  Created at           : 2006/08/08
#  $History:$
#
#---------------------------------------------------------------------

# environment settings
include $(MAKEINC)/default.mk


include $(CONFIGFILE)
include $(MAKEINC)/apps.mk

# install variables
package_init = init.d-configer
package_init_dir = /etc/init.d
package_sbin_dir = /usr/sbin
host_package_sbin_dir=${ROOTFSDIR}$(package_sbin_dir)
host_package_init_dir=${ROOTFSDIR}${package_init_dir}
INSTALLED_APP := $(host_package_sbin_dir)/$(MODNAME).$(EXESUFFIX)
NEW_APP := $(host_package_sbin_dir)/$(MODNAME)

# Targets
all: $(LIBS) $(CUSTOMLIBS) app

install:
	install -C -o root -g root src/${package_init} ${host_package_init_dir}/configer
	install -C -o root -g root $(APPTARGET) $(host_package_sbin_dir)
	$(MV) $(INSTALLED_APP) $(NEW_APP)
	$(STRIP) $(NEW_APP)

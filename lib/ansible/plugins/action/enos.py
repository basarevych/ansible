# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by
# Ansible still belong to the author of the module, and may assign their own
# license to the complete work.
#
# Copyright (C) 2017 Lenovo, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Contains Action Plugin methods for ENOS Modules
# Lenovo Networking

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import copy

from ansible import constants as C
from ansible.plugins.action.normal import ActionModule as _ActionModule
from ansible.module_utils.enos import enos_provider_spec
from ansible.module_utils.network_common import load_provider


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(_ActionModule):

    def run(self, tmp=None, task_vars=None):

        if self._play_context.connection != 'local':
            return dict(
                failed=True,
                msg='invalid connection specified, expected connection=local, '
                    'got %s' % self._play_context.connection
            )
        provider = load_provider(enos_provider_spec, self._task.args)

        pc = copy.deepcopy(self._play_context)
        pc.connection = 'network_cli'
        pc.network_os = 'enos'
        pc.remote_addr = provider['host'] or self._play_context.remote_addr
        display.vvvv('remote_addr: %s' % pc.remote_addr)
        pc.port = provider['port'] or self._play_context.port or 22
        pc.remote_user = provider['username'] or self._play_context.connection_user
        pc.password = provider['password'] or self._play_context.password
        pc.private_key_file = provider['ssh_keyfile'] or self._play_context.private_key_file
        pc.timeout = int(provider['timeout'] or C.PERSISTENT_COMMAND_TIMEOUT)

        pc.become = provider['authorize'] or True
        pc.become_pass = provider['auth_pass']

        display.vvv('using connection plugin %s' % pc.connection, pc.remote_addr)
        connection = self._shared_loader_obj.connection_loader.get('persistent', pc, sys.stdin)

        socket_path = connection.run()

        display.vvvv('socket_path: %s' % socket_path, pc.remote_addr)
        if not socket_path:
            return {'failed': True,
                    'msg': 'unable to open shell. Please see: ' +
                           'https://docs.ansible.com/ansible/network_debug_troubleshooting.html#unable-to-open-shell'}

        task_vars['ansible_socket'] = socket_path

        if self._play_context.become_method == 'enable':
            self._play_context.become = False
            self._play_context.become_method = None

        result = super(ActionModule, self).run(tmp, task_vars)
        return result

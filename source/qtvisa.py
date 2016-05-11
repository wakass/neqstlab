# visa.py, wrapper to support different GPIB controllers
# Reinier Heeres <reinier@heeres.eu>, 2013
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


import logging
import socket
import select

try:
    from pyvisa import SerialInstrument
except:
    pass

_drivers = (
    'pyvisa',
    'visa',
    'prologix_ethernet'
)

def set_visa(name):
    if name not in _drivers:
        raise ValueError('Unknown VISA provider: %s', name)

    try:
        global instrument 

        if name == "pyvisa":
            from pyvisa import visa as module
            instrument=module.instrument
        elif name == 'visa':
            import imp
            fp, pathname, description = imp.find_module(name)
            try:
                module = imp.load_module(name, fp, pathname, description)
            finally:
                if fp:
                    fp.close()   
                     
            instrument = module.ResourceManager('@py')
            instrument = instrument.open_resource
        else:
            module = __import__(name)
            instrument = module.instrument
    except:
        logging.warning('Unable to load visa driver %s', name)

# Set VISA provider
# Make a guess for the default visa provider, linux or windows
import platform
if platform.system() == 'Linux':
   visa_provider = 'visa' 
else:
   visa_provider = 'pyvisa'
import ipdb
ipdb.set_trace()
set_visa(visa_provider)

class TcpIpInstrument:
    '''
    Class to mimic visa instrument for TCP/IP connected text-based devices.
    '''

    def __init__(self, host, port, timeout=20, termchars='\n'):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host, port))

        self._termchars = termchars
        self._timeout = timeout
        self.set_timeout(timeout)

    def set_timeout(self, timeout):
        self._timeout = timeout
        self._socket.settimeout(timeout)

    def set_termchars(self, termchars):
        self._termchars = termchars

    def clear(self):
        rlist, wlist, xlist = select.select([self._socket], [], [], 0)
        if len(rlist) == 0:
            return
        ret = self.read()

    def write(self, data):
        self.clear()
        if not data.endswith(self._termchars):
            data += self._termchars
        self._socket.send(data)

    def read(self, timeout=None):
        if timeout is None:
            timeout = self._timeout
        start = time()
        try:
            ans = ''
            while len(ans) == 0 and (time() - start) < timeout and not ans.endswith(self._termchars):
                ans2 = self._socket.recv(8192)
                ans += ans2
                if len(ans2) == 0:
                    sleep(0.005)
        except socket.timeout, e:
            logging.warning('TCP/IP instrument read timed out')
            return ''

        if ans.endswith(self._termchars):
            ans = ans[:-len(self._termchars)]
        return ans

    def ask(self, data):
        self.clear()
        self.write(data)
        return self.read()


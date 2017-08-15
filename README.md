# PyDirectord
PyDirectord is intended as a replacement for ldirectord. It is based on the Twisted framework and written using Python 3. Currently it is still a work in progress with a limited amount of features. Eventually, it is to include at least a similar amount of different checks as ldirectord.

## Dependencies
PyDirectord has the following Python dependencies:
* Python (version 3.4 or newer)
* Twisted (version 17.5.0 or newer)
* pyOpenSSL
* service\_identity
* idna
* mysqlclient
* PyGreSQL
* (ldaptor)

The latter is used in `checks/ldap.py` which is not yet working because it is not yet available for Python 3.

PyDirectord relies on the Linux Virtual Server (LVS) of the Kernel. The following package will have to be installed on Debian-based systems:
* ipvsadm

In addition to that, a number of software libraries from the distribution repositories are needed to install the Python dependencies (using `pip3`) mentioned earlier. These include but might not be limited to:
* libssl-dev
* libmysqlclient-dev
* libpq-dev

## License
PyDirectord is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

PyDirectord is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with PyDirectord.  If not, see <http://www.gnu.org/licenses/>.

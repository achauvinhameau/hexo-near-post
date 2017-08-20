#
# Time-stamp: <2017-08-20 14:09:03 alex>
#
# --------------------------------------------------------------------
# hexo-near-post
#
# Copyright (C) 2016-2017  Alexandre Chauvin Hameau <ach@meta-x.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------

dirs = 
PYTHON = python

all:
	@echo make clean
	@echo make lint
	@echo make flakes
	@echo make version

lint: clean
	@pylint --rcfile=~/.pylint *.py

flakes: clean
	@pyflakes *.py

cc: clean
	@echo '* complexity *'
	@RADONFILESENCODING=UTF-8 radon cc $(dirs) *py -a -nc
	@echo '* maintenability *'
	@RADONFILESENCODING=UTF-8 radon mi $(dirs) *py -nb

clean:
	@rm -f *pyc *~

version:
	@awk '/^__version/ { $$0="__version__ = \"'`cat VERSION`'\"" }; /^__date__/ { $$0="__date__ = \"'`date +%0d/%0m/%Y-%H:%M:%S`'\"" } ; { print }' < hexo-nearest-compute.py > /tmp/hexo-nearest-compute.py
	@cp /tmp/hexo-nearest-compute.py .
	@rm -f /tmp/hexo-nearest-compute.py


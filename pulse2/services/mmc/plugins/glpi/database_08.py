# -*- coding: utf-8; -*-
#
# (c) 2004-2007 Linbox / Free&ALter Soft, http://linbox.com
# (c) 2007-2010 Mandriva, http://www.mandriva.com
#
# $Id$
#
# This file is part of Mandriva Management Console (MMC).
#
# MMC is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# MMC is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with MMC.  If not, see <http://www.gnu.org/licenses/>.

"""
This module declare all the necessary stuff to connect to a glpi database in it's
version 0.8x
"""

# TODO rename location into entity (and locations in location)
from mmc.plugins.glpi.config import GlpiConfig
from mmc.plugins.glpi.utilities import complete_ctx
from pulse2.utils import same_network, unique
from pulse2.database.dyngroup.dyngroup_database_helper import DyngroupDatabaseHelper
from pulse2.managers.group import ComputerGroupManager
from mmc.plugins.glpi.database_utils import decode_latin1, encode_latin1, decode_utf8, encode_utf8, fromUUID, toUUID, setUUID
from mmc.plugins.glpi.database_utils import DbTOA

from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.sql import union

import logging
import re
from sets import Set
import exceptions

class Glpi08(DyngroupDatabaseHelper):
    """
    Singleton Class to query the glpi database in version > 0.80.

    """
    is_activated = False

    def db_check(self):
        self.my_name = "Glpi"
        self.configfile = "glpi.ini"
        return DyngroupDatabaseHelper.db_check(self)

    def try_activation(self, config):
        """
        function to see if that glpi database backend is the one we need to use
        """
        self.config = config
        dburi = self.makeConnectionPath()
        self.db = create_engine(dburi, pool_recycle = self.config.dbpoolrecycle, pool_size = self.config.dbpoolsize)
        try:
            glpi_version = self.db.execute('SELECT version FROM glpi_configs').fetchone().values()[0].replace(' ', '')
        except Exception, e:
            logging.getLogger().error(e)
            return False
        return True

    def glpi_version(self):
        return self._glpi_version

    def glpi_version_new(self):
        return False

    def glpi_chosen_version(self):
        return "0.8"

    def activate(self, config = None):
        self.logger = logging.getLogger()
        DyngroupDatabaseHelper.init(self)
        if self.is_activated:
            self.logger.info("Glpi don't need activation")
            return None
        self.logger.info("Glpi is activating")
        if config != None:
            self.config = config
        else:
            self.config = GlpiConfig("glpi", conffile)
        dburi = self.makeConnectionPath()
        self.db = create_engine(dburi, pool_recycle = self.config.dbpoolrecycle, pool_size = self.config.dbpoolsize)
        try:
            self.db.execute(u'SELECT "\xe9"')
            setattr(Glpi08, "decode", decode_utf8)
            setattr(Glpi08, "encode", encode_utf8)
        except:
            self.logger.warn("Your database is not in utf8, will fallback in latin1")
            setattr(Glpi08, "decode", decode_latin1)
            setattr(Glpi08, "encode", encode_latin1)
        self._glpi_version = self.db.execute('SELECT version FROM glpi_configs').fetchone().values()[0].replace(' ', '')
        self.metadata = MetaData(self.db)
        self.initMappers()
        self.logger.info("Glpi is in version %s" % (self.glpi_version()))
        self.metadata.create_all()
        self.is_activated = True
        self.logger.debug("Glpi finish activation")
        return True

    def getTableName(self, name):
        return ''.join(map(lambda x:x.capitalize(), name.split('_')))

    def initMappers(self):
        """
        Initialize all SQLalchemy mappers needed for the inventory database
        """

        self.klass = {}

        # simply declare some tables (that dont need and FK relations, or anything special to declare)
        for i in ('glpi_operatingsystemversions', 'glpi_computertypes', 'glpi_operatingsystems', 'glpi_operatingsystemservicepacks', 'glpi_operatingsystemversions', 'glpi_domains', \
                'glpi_computermodels', 'glpi_networks'):
            setattr(self, i, Table(i, self.metadata, autoload = True))
            j = self.getTableName(i)
            exec "class %s(DbTOA): pass" % j
            mapper(eval(j), getattr(self, i))
            self.klass[i] = eval(j)

        # declare all the glpi_device* and glpi_computer_device*
        # two of these tables have a nomenclature one (devicecasetypes and devicememorytypes) but we dont need it for the moment.
        self.devices = ('devicecases', 'devicecontrols', 'devicedrives', 'devicegraphiccards', 'deviceharddrives', 'devicememories', \
                        'devicemotherboards', 'devicenetworkcards', 'devicepcis', 'devicepowersupplies', 'deviceprocessors', 'devicesoundcards')
        for i in self.devices:
            setattr(self, i, Table("glpi_%s"%i, self.metadata, autoload = True))
            j = self.getTableName(i)
            exec "class %s(DbTOA): pass" % j
            mapper(eval(j), getattr(self, i))
            self.klass[i] = eval(j)

            setattr(self, "computers_%s"%i, Table("glpi_computers_%s"%i, self.metadata,
                Column('computers_id', Integer, ForeignKey('glpi_computers.id')),
                Column('%s_id'%i, Integer, ForeignKey('glpi_%s.id'%i)),
                autoload = True))
            j = self.getTableName("computers_%s"%i)
            exec "class %s(DbTOA): pass" % j
            mapper(eval(j), getattr(self, "computers_%s"%i))
            self.klass["computers_%s"%i] = eval(j)

        # entity
        self.location = Table("glpi_entities", self.metadata, autoload = True)
        mapper(Location, self.location)

        # location
        self.locations = Table("glpi_locations", self.metadata, autoload = True)
        mapper(Locations, self.locations)

        # processor
        self.processor = Table("glpi_deviceprocessors", self.metadata, autoload = True)
        mapper(Processor, self.processor)

        # network # TODO take care with the itemtype should we always set it to Computer?
        self.network = Table("glpi_networkports", self.metadata,
            Column('items_id', Integer, ForeignKey('glpi_computers.id')),
            autoload = True)
        mapper(Network, self.network)

        self.net = Table("glpi_networks", self.metadata, autoload = True)
        mapper(Net, self.net)

        # os
        self.os = Table("glpi_operatingsystems", self.metadata, autoload = True)
        mapper(OS, self.os)

        self.os_sp = Table("glpi_operatingsystemservicepacks", self.metadata, autoload = True)
        mapper(OsSp, self.os_sp)

        # domain
        self.domain = Table('glpi_domains', self.metadata, autoload = True)
        mapper(Domain, self.domain)

        # machine (we need the foreign key, so we need to declare the table by hand ...
        #          as we don't need all columns, we don't declare them all)
        self.machine = Table("glpi_computers", self.metadata,
            Column('id', Integer, primary_key=True),
            Column('entities_id', Integer, ForeignKey('glpi_entities.id')),
            Column('operatingsystems_id', Integer, ForeignKey('glpi_operatingsystems.id')),
            Column('operatingsystemversions_id', Integer, ForeignKey('glpi_operatingsystemversions.id')),
            Column('operatingsystemservicepacks_id', Integer, ForeignKey('glpi_operatingsystemservicepacks.id')),
            Column('locations_id', Integer, ForeignKey('glpi_locations.id')),
            Column('domains_id', Integer, ForeignKey('glpi_domains.id')),
            Column('networks_id', Integer, ForeignKey('glpi_networks.id')),
            Column('computermodels_id', Integer, ForeignKey('glpi_computermodels.id')),
            Column('computertypes_id', Integer, ForeignKey('glpi_computertypes.id')),
            Column('groups_id', Integer, ForeignKey('glpi_groups.id')),
            #Column('FK_glpi_enterprise', Integer, ForeignKey('glpi_enterprises.id')),
            Column('name', String(255), nullable=False),
            Column('serial', String(255), nullable=False),
            Column('os_license_number', String(255), nullable=True),
            Column('os_licenseid', String(255), nullable=True),
            Column('is_deleted', Integer, nullable=False),
            Column('is_template', Integer, nullable=False),
            Column('states_id', Integer, nullable=False), #ForeignKey('glpi_states.id')),
            Column('comment', String(255), nullable=False),
            autoload = True)
        mapper(Machine, self.machine) #, properties={'entities_id': relation(Location)})

        # profile
        self.profile = Table("glpi_profiles", self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(255), nullable=False))
        mapper(Profile, self.profile)

        # user
        self.user = Table("glpi_users", self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(255), nullable=False),
            Column('auths_id', Integer, nullable=False),
            Column('is_deleted', Integer, nullable=False),
            Column('is_active', Integer, nullable=False))
        mapper(User, self.user)

        # userprofile
        self.userprofile = Table("glpi_profiles_users", self.metadata,
            Column('id', Integer, primary_key=True),
            Column('users_id', Integer, ForeignKey('glpi_users.id')),
            Column('profiles_id', Integer, ForeignKey('glpi_profiles.id')),
            Column('entities_id', Integer, ForeignKey('glpi_entities.id')),
            Column('is_recursive', Integer))
        mapper(UserProfile, self.userprofile)

        # software
        self.software = Table("glpi_softwares", self.metadata, autoload = True)
        mapper(Software, self.software)

        # glpi_inst_software
        self.inst_software = Table("glpi_computers_softwareversions", self.metadata,
            Column('computers_id', Integer, ForeignKey('glpi_computers.id')),
            Column('softwareversions_id', Integer, ForeignKey('glpi_softwareversions.id')),
            autoload = True)
        mapper(InstSoftware, self.inst_software)

        # glpi_licenses
        self.licenses = Table("glpi_softwarelicenses", self.metadata,
            Column('softwares_id', Integer, ForeignKey('glpi_softwares.id')),
            autoload = True)
        mapper(Licenses, self.licenses)

        # glpi_softwareversions
        self.softwareversions = Table("glpi_softwareversions", self.metadata,
                Column('softwares_id', Integer, ForeignKey('glpi_softwares.id')),
                autoload = True)
        mapper(SoftwareVersion, self.softwareversions)

        # model
        self.model = Table("glpi_computermodels", self.metadata, autoload = True)
        mapper(Model, self.model)

        # group
        self.group = Table("glpi_groups", self.metadata, autoload = True)
        mapper(Group, self.group)

    ##################### internal query generators
    def __filter_on(self, query):
        """
        Use the glpi.ini conf parameter filter_on to filter machines on some parameters
        The request is in OR not in AND, so be carefull with what you want
        """
        ret = self.__filter_on_filter(query)
        if type(ret) == type(None):
            return query
        else:
            return query.filter(ret)

    def __filter_on_filter(self, query):
        if self.config.filter_on != None:
            a_filter_on = []
            for filter_key, filter_value in self.config.filter_on:
                if filter_key == 'state':
                    self.logger.debug('will filter %s == %s' % (filter_key, filter_value))
                    a_filter_on.append(self.machine.c.states_id == filter_value)
                else:
                    self.logger.warn('dont know how to filter on %s' % (filter_key))
            if len(a_filter_on) == 0:
                return None
            elif len(a_filter_on) == 1:
                return a_filter_on[0]
            else:
                return or_(*a_filter_on)
        return None

    def __filter_on_entity(self, query, ctx, other_locids = []):
        ret = self.__filter_on_entity_filter(query, ctx, other_locids)
        return query.filter(ret)

    def __filter_on_entity_filter(self, query, ctx, other_locids = []):
        # FIXME: I put the locationsid in the security context to optimize the
        # number of requests. locationsid is set by
        # glpi.utilities.complete_ctx, but when querying via the dyngroup
        # plugin it is not called.
        if not hasattr(ctx, 'locationsid'):
            complete_ctx(ctx)
        return self.machine.c.entities_id.in_(ctx.locationsid + other_locids)

    def __getRestrictedComputersListQuery(self, ctx, filt = None, session = create_session()):
        """
        Get the sqlalchemy query to get a list of computers with some filters
        """
        if session == None:
            session = create_session()
        query = session.query(Machine)
        query = self.__filter_on(query)
        if filt:
            # filtering on query
            join_query = self.machine
            query_filter = None

            filters = [self.machine.c.is_deleted == 0, self.machine.c.is_template == 0, self.__filter_on_filter(query), self.__filter_on_entity_filter(query, ctx)]

            join_query, query_filter = self.filter(ctx, self.machine, filt, session.query(Machine), self.machine.c.id, filters)

            # filtering on locations
            try:
                location = filt['location']
                if location == '' or location == u'' or not self.displayLocalisationBar:
                    location = None
            except KeyError:
                location = None

            try:
                ctxlocation = filt['ctxlocation']
                if not self.displayLocalisationBar:
                    ctxlocation = None
            except KeyError:
                ctxlocation = None

            if ctxlocation != None:
                locsid = []
                locs = []
                if type(ctxlocation) == list:
                    for loc in ctxlocation:
                        locs.append(self.__getName(loc))
                        locsid.append(self.__getId(loc))
                join_query = join_query.join(self.location)

                if location != None:
                    locationid = int(location.replace('UUID', ''))
                    location = self.__getName(location)
                    try:
                        self.logger.warn(locsid)
                        self.logger.warn(locationid)
                        locsid.index(locationid) # just check that location is in locs, or throw an exception
                        query_filter = self.__addQueryFilter(query_filter, (self.location.c.name == location))
                    except ValueError:
                        self.logger.warn("User '%s' is trying to get the content of an unauthorized entity : '%s'" % (ctx.userid, location))
                        session.close()
                        return None
                else:
                    query_filter = self.__addQueryFilter(query_filter, self.location.c.name.in_(locs))
            elif location != None:
                join_query = join_query.join(self.location)

                location = self.__getName(location)
                query_filter = self.__addQueryFilter(query_filter, (self.location.c.name == location))
            query = query.select_from(join_query).filter(query_filter)
            query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
            query = self.__filter_on(query)
            query = self.__filter_on_entity(query, ctx)

            # filtering on machines (name or uuid)
            try:
                query = query.filter(self.machine.c.name.like(filt['hostname']+'%'))
            except KeyError:
                pass
            try:
                query = query.filter(self.machine.c.name.like(filt['name']+'%'))
            except KeyError:
                pass
            try:
                query = query.filter(self.machine.c.name.like(filt['filter']+'%'))
            except KeyError:
                pass

            try:
                query = self.filterOnUUID(query, filt['uuid'])
            except KeyError:
                pass

            if 'uuids' in filt and type(filt['uuids']) == list and len(filt['uuids']) > 0:
                query = self.filterOnUUID(query, filt['uuids'])

            try:
                gid = filt['gid']
                machines = []
                if ComputerGroupManager().isrequest_group(ctx, gid):
                    machines = map(lambda m: fromUUID(m), ComputerGroupManager().requestresult_group(ctx, gid, 0, -1, ''))
                else:
                    machines = map(lambda m: fromUUID(m), ComputerGroupManager().result_group(ctx, gid, 0, -1, ''))
                query = query.filter(self.machine.c.id.in_(machines))

            except KeyError:
                pass

            try:
                request = filt['request']
                bool = None
                if filt.has_key('equ_bool'):
                    bool = filt['equ_bool']
                machines = map(lambda m: fromUUID(m), ComputerGroupManager().request(ctx, request, bool, 0, -1, ''))
                query = query.filter(self.machine.c.id.in_(machines))
            except KeyError, e:
                pass

        return query

    def __getId(self, obj):
        if type(obj) == dict:
            return obj['uuid']
        if type(obj) != str and type(obj) != unicode:
            return obj.id
        return obj

    def __getName(self, obj):
        if type(obj) == dict:
            return obj['name']
        if type(obj) != str and type(obj) != unicode:
            return obj.name
        if type(obj) == str and re.match('UUID', obj):
            l = self.getLocation(obj)
            if l: return l.name
        return obj

    def __addQueryFilter(self, query_filter, eq):
        if str(query_filter) == str(None): # don't remove the str, sqlalchemy.sql._BinaryExpression == None return True!
            query_filter = eq
        else:
            query_filter = and_(query_filter, eq)
        return query_filter

    def computersTable(self):
        return [self.machine]

    def computersMapping(self, computers, invert = False):
        if not invert:
            return Machine.id.in_(map(lambda x:fromUUID(x), computers))
        else:
            return Machine.id.not_(in_(map(lambda x:fromUUID(x), computers)))

    def mappingTable(self, ctx, query):
        """
        Map a table name on a table mapping
        """
        base = []
        if ctx.userid != 'root':
            base.append(self.location)
        if query[2] == 'OS':
            return base + [self.os]
        elif query[2] == 'ENTITY':
            return base + [self.location]
        elif query[2] == 'SOFTWARE':
            return base + [self.inst_software, self.licenses, self.software]
        elif query[2] == 'Nom':
            return base
        elif query[2] == 'Contact':
            return base
        elif query[2] == 'Numero du contact':
            return base
        elif query[2] == 'Comments':
            return base
        elif query[2] == 'Modele':
            return base + [self.model]
        elif query[2] == 'Lieu':
            return base + [self.locations]
        elif query[2] == 'OS':
            return base + [self.os]
        elif query[2] == 'ServicePack':
            return base + [self.os_sp]
        elif query[2] == 'Groupe':
            return base + [self.group]
        elif query[2] == 'Reseau':
            return base + [self.net]
        elif query[2] == 'Logiciel':
            return base + [self.inst_software, self.softwareversions, self.software]
        elif query[2] == 'Version':
            return base + [self.inst_software, self.softwareversions, self.software]
        return []

    def mapping(self, ctx, query, invert = False):
        """
        Map a name and request parameters on a sqlalchemy request
        """
        if len(query) == 4:
            # in case the glpi database is in latin1, don't forget dyngroup is in utf8
            # => need to convert what comes from the dyngroup database
            query[3] = self.encode(query[3])
            r1 = re.compile('\*')
            like = False
            if type(query[3]) == list:
                q3 = []
                for q in query[3]:
                    if r1.search(q):
                        like = True
                        q = r1.sub('%', q)
                    q3.append(q)
                query[3] = q3
            else:
                if r1.search(query[3]):
                    like = True
                    query[3] = r1.sub('%', query[3])

            parts = self.__getPartsFromQuery(query)
            ret = []
            for part in parts:
                partA, partB = part
                if invert:
                    if like:
                        ret.append(not_(partA.like(self.encode(partB))))
                    else:
                        ret.append(partA != self.encode(partB))
                else:
                    if like:
                        ret.append(partA.like(self.encode(partB)))
                    else:
                        ret.append(partA == self.encode(partB))
            if ctx.userid != 'root':
                ret.append(self.__filter_on_entity_filter(None, ctx))
            return and_(*ret)
        else:
            return self.__treatQueryLevel(query)

    def __getPartsFromQuery(self, query):
        if query[2] == 'OS':
            return [[self.os.c.name, query[3]]]
        elif query[2] == 'ENTITY':
            return [[self.location.c.name, query[3]]]
        elif query[2] == 'SOFTWARE':
            return [[self.software.c.name, query[3]]]
        elif query[2] == 'Nom':
            return [[self.machine.c.name, query[3]]]
        elif query[2] == 'Contact':
            return [[self.machine.c.contact, query[3]]]
        elif query[2] == 'Numero du contact':
            return [[self.machine.c.contact_num, query[3]]]
        elif query[2] == 'Comments':
            return [[self.machine.c.comment, query[3]]]
        elif query[2] == 'Modele':
            return [[self.model.c.name, query[3]]]
        elif query[2] == 'Lieu':
            return [[self.locations.c.completename, query[3]]]
        elif query[2] == 'ServicePack':
            return [[self.os_sp.c.name, query[3]]]
        elif query[2] == 'Groupe': # TODO double join on ENTITY
            return [[self.group.c.name, query[3]]]
        elif query[2] == 'Reseau':
            return [[self.net.c.name, query[3]]]
        elif query[2] == 'Logiciel': # TODO double join on ENTITY
            return [[self.software.c.name, query[3]]]
        elif query[2] == 'Version': # TODO double join on ENTITY
            return [[self.software.c.name, query[3][0]], [self.softwareversions.c.name, query[3][1]]]
        return []


    def __getTable(self, table):
        if table == 'OS':
            return self.os.c.name
        elif table == 'ENTITY':
            return self.location.c.name
        elif table == 'SOFTWARE':
            return self.software.c.name
        raise Exception("dont know table for %s"%(table))

    ##################### machine list management
    def getComputer(self, ctx, filt):
        """
        Get the first computers that match filters parameters
        """
        ret = self.getRestrictedComputersList(ctx, 0, 10, filt)
        if len(ret) != 1:
            for i in ['location', 'ctxlocation']:
                try:
                    filt.pop(i)
                except:
                    pass
            ret = self.getRestrictedComputersList(ctx, 0, 10, filt)
            if len(ret) > 0:
                raise Exception("NOPERM##%s" % (ret[0][1]['fullname']))
            return False
        return ret.values()[0]

    def getRestrictedComputersListLen(self, ctx, filt = None):
        """
        Get the size of the computer list that match filters parameters
        """
        session = create_session()
        query = self.__getRestrictedComputersListQuery(ctx, filt, session)
        if query == None:
            return 0
        query = query.group_by([self.machine.c.name, self.machine.c.domains_id])
        ret = query.count()
        session.close()
        return ret

    def getRestrictedComputersList(self, ctx, min = 0, max = -1, filt = None, advanced = True, justId = False, toH = False):
        """
        Get the computer list that match filters parameters between min and max

        FIXME: may return a list or a dict according to the parameters
        """
        session = create_session()
        ret = {}

        query = self.__getRestrictedComputersListQuery(ctx, filt, session)
        if query == None:
            return {}

        query = query.group_by([self.machine.c.name, self.machine.c.domains_id]).order_by(asc(self.machine.c.name))

        if min != 0:
            query = query.offset(min)
        if max != -1:
            max = int(max) - int(min)
            query = query.limit(max)

        if justId:
            ret = map(lambda m: self.getMachineUUID(m), query.all())
        elif toH:
            ret = map(lambda m: m.toH(), query.all())
        else:
            if filt.has_key('get'):
                ret = self.__formatMachines(query.all(), advanced, filt['get'])
            else:
                ret = self.__formatMachines(query.all(), advanced)
        session.close()
        return ret

    def getTotalComputerCount(self):
        session = create_session()
        query = session.query(Machine)
        query = self.__filter_on(query)
        c = query.count()
        session.close()
        return c

    def getComputerCount(self, ctx, filt = None):
        """
        Same as getRestrictedComputersListLen
        TODO : remove this one
        """
        return self.getRestrictedComputersListLen(ctx, filt)

    def getComputersList(self, ctx, filt = None):
        """
        Same as getRestrictedComputersList without limits
        """
        return self.getRestrictedComputersList(ctx, 0, -1, filt)

    ##################### UUID policies
    def getMachineUUID(self, machine):
        """
        Get this machine UUID
        """
        return toUUID(str(machine.id))

    def getMachineByUUID(self, uuid):
        """
        Get the machine that as this UUID
        """
        session = create_session()
        ret = session.query(Machine).filter(self.machine.c.id == int(str(uuid).replace("UUID", "")))
        ret = ret.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        ret = self.__filter_on(ret).first()
        session.close()
        return ret

    def filterOnUUID(self, query, uuid):
        """
        Modify the given query to filter on the machine UUID
        """
        if type(uuid) == list:
            return query.filter(self.machine.c.id.in_(map(lambda a:int(str(a).replace("UUID", "")), uuid)))
        else:
            return query.filter(self.machine.c.id == int(str(uuid).replace("UUID", "")))

    ##################### Machine output format (for ldap compatibility)
    def __getAttr(self, machine, get):
        ma = {}
        for field in get:
            if hasattr(machine, field):
                ma[field] = getattr(machine, field)
            if field == 'uuid' or field == 'objectUUID':
                ma[field] = toUUID(str(machine.id))
            if field == 'cn':
                ma[field] = machine.name
        return ma

    def __formatMachines(self, machines, advanced, get = None):
        """
        Give an LDAP like version of machines
        """
        ret = {}
        if get != None:
            for m in machines:
                ret[m.getUUID()] = self.__getAttr(m, get)
            return ret

        names = {}
        for m in machines:
            ret[m.getUUID()] = [None, {
                'cn': [m.name],
                'displayName': [m.comment],
                'objectUUID': [m.getUUID()]
            }]
            names[m.getUUID()] = m.name
        if advanced:
            uuids = map(lambda m: m.getUUID(), machines)
            nets = self.getMachinesNetwork(uuids)
            for uuid in ret:
                try:
                    (ret[uuid][1]['macAddress'], ret[uuid][1]['ipHostNumber'], ret[uuid][1]['subnetMask'], ret[uuid][1]['domain'], ret[uuid][1]['networkUuids']) = self.orderIpAdresses(uuid, names[uuid], nets[uuid])
                    if ret[uuid][1]['domain'] != '':
                        ret[uuid][1]['fullname'] = ret[uuid][1]['cn'][0]+'.'+ret[uuid][1]['domain'][0]
                    else:
                        ret[uuid][1]['fullname'] = ret[uuid][1]['cn'][0]
                except KeyError, e:
                    ret[uuid][1]['macAddress'] = []
                    ret[uuid][1]['ipHostNumber'] = []
                    ret[uuid][1]['subnetMask'] = []
                    ret[uuid][1]['domain'] = ''
                    ret[uuid][1]['fullname'] = ret[uuid][1]['cn'][0]
        return ret

    def __formatMachine(self, machine, advanced, get = None):
        """
        Give an LDAP like version of the machine
        """

        uuid = self.getMachineUUID(machine)

        if get != None:
            return self.__getAttr(machine, get)

        ret = {
            'cn': [machine.name],
            'displayName': [machine.comment],
            'objectUUID': [uuid]
        }
        if advanced:
            (ret['macAddress'], ret['ipHostNumber'], ret['subnetMask'], domain, ret['networkUuids']) = self.orderIpAdresses(uuid, machine.name, self.getMachineNetwork(uuid))
            if domain == None:
                domain = ''
            elif domain != '':
                domain = '.'+domain
            ret['fullname'] = machine.name + domain
        return [None, ret]

    ##################### entities, profiles and user rigths management
    def displayLocalisationBar(self):
        """
        This module know how to give data to localisation bar
        """
        return True

    def getUserProfile(self, user):
        """
        @return: Return the first user GLPI profile as a string, or None
        """
        session = create_session()
        qprofile = session.query(Profile).select_from(self.profile.join(self.userprofile).join(self.user)).filter(self.user.c.name == user).first()
        if qprofile == None:
            ret = None
        else:
            ret= qprofile.name
        session.close()
        return ret

    def getUserProfiles(self, user):
        """
        @return: Return all user GLPI profiles as a list of string, or None
        """
        session = create_session()
        profiles = session.query(Profile).select_from(self.profile.join(self.userprofile).join(self.user)).filter(self.user.c.name == user)
        if profiles:
            ret = []
            for profile in profiles:
                ret.append(profile.name)
        else:
            ret = None
        session.close()
        return ret

    def getUserParentLocations(self, user):
        """
        get
        return: the list of user locations'parents
        """
        pass

    def getUserLocation(self, user):
        """
        @return: Return one user GLPI entities as a list of string, or None
        TODO : check it is still used!
        """
        session = create_session()
        qlocation = session.query(Location).select_from(self.location.join(self.userprofile).join(self.user)).filter(self.user.c.name == user).first()
        if qlocation == None:
            ret = None
        else:
            ret = qlocation.name
        return ret

    def getUserLocations(self, user):
        """
        Get the GPLI user locations.

        @return: the list of user locations
        @rtype: list
        """
        ret = []
        if user == 'root':
            ret = self.__get_all_locations()
        else:
            # check if user is linked to the root entity
            # (which is not declared explicitly in glpi...
            # we have to emulate it...)
            session = create_session()
            entids = session.query(UserProfile).select_from(self.userprofile.join(self.user).join(self.profile)).filter(self.user.c.name == user).filter(self.profile.c.name.in_(self.config.activeProfiles)).all()
            for entid in entids:
                if entid.entities_id == 0 and entid.is_recursive == 1:
                    session.close()
                    return self.__get_all_locations()

            # the normal case...
            plocs = session.query(Location).add_column(self.userprofile.c.is_recursive).select_from(self.location.join(self.userprofile).join(self.user).join(self.profile)).filter(self.user.c.name == user).filter(self.profile.c.name.in_(self.config.activeProfiles)).all()
            for ploc in plocs:
                if ploc[1]:
                    # The user profile link to the location is recursive, and so
                    # the children locations should be added too
                    for l in self.__add_children(ploc[0]):
                        ret.append(l)
                else:
                    ret.append(ploc[0])
            if len(ret) == 0:
                ret = []
            session.close()

        ret = map(lambda l: setUUID(l), ret)
        return ret

    def __get_all_locations(self):
        ret = []
        session = create_session()
        q = session.query(Location).group_by(self.location.c.name).order_by(asc(self.location.c.completename)).all()
        session.close()
        for location in q:
            ret.append(location)
        return ret

    def __add_children(self, child):
        """
        Recursive function used by getUserLocations to get entities tree if needed
        """
        session = create_session()
        children = session.query(Location).filter(self.location.c.entities_id == child.id).all()
        ret = [child]
        for c in children:
            for res in self.__add_children(c):
                ret.append(res)
        session.close()
        return ret

    def getLocation(self, uuid):
        """
        Get a Location by it's uuid
        """
        session = create_session()
        ret = session.query(Location).filter(self.location.c.id == uuid.replace('UUID', '')).first()
        session.close()
        return ret

    def getLocationsList(self, ctx, filt = None):
        """
        Get the list of all entities that user can access
        """
        ret = []
        complete_ctx(ctx)
        filtr = re.compile(filt)
        for loc in ctx.locations:
            if filt:
                if filtr.search(loc.name):
                    ret.append(loc.name)
            else:
                ret.append(loc.name)

        return ret

    def getLocationsCount(self):
        """
        Returns the total count of locations
        """
        session = create_session()
        ret = session.query(Location).count()
        session.close()
        return ret

    def getMachinesLocations(self, machine_uuids):
        session = create_session()
        q = session.query(Location).add_column(self.machine.c.id).select_from(self.location.join(self.machine)).filter(self.machine.c.id.in_(map(fromUUID, machine_uuids))).all()
        session.close()
        ret = {}
        for loc, mid in q:
            ret[toUUID(mid)] = loc.toH()
        return ret

    def getUsersInSameLocations(self, userid, locations = None):
        """
        Returns all users name that share the same locations with the given
        user
        """
        if locations == None:
            locations = self.getUserLocations(userid)
        ret = []
        if locations:
            inloc = []
            for location in locations:
                inloc.append(location.name)
            session = create_session()
            q = session.query(User).select_from(self.user.join(self.userprofile).join(self.location)).filter(self.location.c.name.in_(inloc)).filter(self.user.c.name != userid).distinct().all()
            session.close()
            # Only returns the user names
            ret = map(lambda u: u.name, q)
        # Always append the given userid
        ret.append(userid)
        return ret

    def getComputerInLocation(self, location = None):
        """
        Get all computers in that location
        """
        session = create_session()
        query = session.query(Machine).select_from(self.machine.join(self.location)).filter(self.location.c.name == location)
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        ret = []
        for machine in query.group_by(self.machine.c.name).order_by(asc(self.machine.c.name)):
            ret[machine.name] = self.__formatMachine(machine)
        session.close()
        return ret

    def getLocationsFromPathString(self, location_path):
        """
        """
        session = create_session()
        ens = []
        for loc_path in location_path:
            loc_path = " > ".join(loc_path)
            q = session.query(Location).filter(self.location.c.completename == loc_path).all()
            if len(q) != 1:
                ens.append(False)
            else:
                ens.append(toUUID(str(q[0].id)))
        session.close()
        return ens

    def getLocationParentPath(self, loc_uuid):
        session = create_session()
        path = []
        en_id = fromUUID(loc_uuid)
        en = session.query(Location).filter(self.location.c.id == en_id).first()
        parent_id = en.entities_id

        while parent_id != 0:
            en_id = parent_id
            en = session.query(Location).filter(self.location.c.id == parent_id).first()
            path.append(toUUID(en.id))
            parent_id = en.entities_id
        path.append('UUID0')
        return path

    def doesUserHaveAccessToMachines(self, ctx, a_machine_uuid, all = True):
        """
        Check if the user has correct permissions to access more than one or to all machines

        Return always true for the root user.

        @rtype: bool
        """
        if not self.displayLocalisationBar:
            return True

        session = create_session()
        # get the number of computers the user have access to
        query = session.query(Machine)
        if ctx.userid == "root":
            query = self.filterOnUUID(query, a_machine_uuid)
        else:
            a_locations = map(lambda loc:loc.name, ctx.locations)
            query = query.select_from(self.machine.join(self.location))
            query = query.filter(self.location.c.name.in_(a_locations))
            query = self.filterOnUUID(query, a_machine_uuid)
        ret = query.group_by(self.machine.c.id).all()
        # get the number of computers that had not been deleted
        machines_uuid_size = len(a_machine_uuid)
        all_computers = session.query(Machine)
        all_computers = self.filterOnUUID(all_computers, a_machine_uuid).all()
        all_computers = Set(map(lambda m:toUUID(str(m.id)), all_computers))
        if len(all_computers) != machines_uuid_size:
            self.logger.info("some machines have been deleted since that list was generated (%s)"%(str(Set(a_machine_uuid) - all_computers)))
            machines_uuid_size = len(all_computers)
        size = 1
        if type(ret) == list:
            size = len(ret)
        if all and size == machines_uuid_size:
            return True
        elif (not all) and machines_uuid_size == 0:
            return True
        elif (not all) and len(ret) > 0:
            return True
        ret = Set(map(lambda m:toUUID(str(m.id)), ret))
        self.logger.info("dont have permissions on %s"%(str(Set(a_machine_uuid) - ret)))
        return False

    def doesUserHaveAccessToMachine(self, ctx, machine_uuid):
        """
        Check if the user has correct permissions to access this machine

        @rtype: bool
        """
        return self.doesUserHaveAccessToMachines(ctx, [machine_uuid])

    ##################### for inventory purpose (use the same API than OCSinventory to keep the same GUI)
    def getAllDevices(self, uuid):
        my_union = []
        session = create_session()
        for i in self.devices:
            glpi_table = getattr(self, 'computers_%s'%(i))
            my_union.append(select([glpi_table.c.id, getattr(glpi_table.c, "%s_id"%i), func.concat('', i).label('type')], glpi_table.c.computers_id == fromUUID(uuid)))
        query = union(*my_union)

        conn = self.getDbConnection()
        query = conn.execute(query).fetchall()
        conn.close()

        session.close()
        ret = []
        query.sort(lambda x, y: cmp(x[2], y[2]))
        for i in query:
            ret.append(self.getDeviceByType(i[1], i[2]))
        return ret

    def getDeviceByType(self, did, device_type):
        k = getattr(self, device_type)
        klass = self.klass[device_type]
        session = create_session()
        query = session.query(klass).filter(k.id == did).first()
        session.close()
        ret = query.to_a()
        ret.append(['type', device_type.replace('device', '')])
        return ret

    def getLastMachineInventoryFull(self, uuid):
        session = create_session()
        # there is glpi_entreprise missing
        query = self.filterOnUUID(session.query(Machine) \
                .add_column(self.glpi_operatingsystems.c.name) \
                .add_column(self.glpi_operatingsystemservicepacks.c.name) \
                .add_column(self.glpi_operatingsystemversions.c.name) \
                .add_column(self.glpi_domains.c.name) \
                .add_column(self.locations.c.name) \
                .add_column(self.glpi_computermodels.c.name) \
                .add_column(self.glpi_computertypes.c.name) \
                .add_column(self.glpi_networks.c.name) \
                .add_column(self.location.c.completename) \
                .select_from( \
                        self.machine.outerjoin(self.glpi_operatingsystems).outerjoin(self.glpi_operatingsystemservicepacks).outerjoin(self.glpi_operatingsystemversions).outerjoin(self.glpi_computertypes) \
                        .outerjoin(self.glpi_domains).outerjoin(self.locations).outerjoin(self.glpi_computermodels).outerjoin(self.glpi_networks) \
                        .join(self.location)
                ), uuid).all()
        ret = []
        ind = {'os':1, 'os_sp':2, 'os_version':3, 'type':7, 'domain':4, 'location':5, 'model':6, 'network':8, 'entity':9} # 'entreprise':9
        for m in query:
            ma1 = m[0].to_a()
            ma2 = []
            for x,y in ma1:
                if x in ind.keys():
                    ma2.append([x,m[ind[x]]])
                else:
                    ma2.append([x,y])
            ret.append(ma2)
        if type(uuid) == list:
            return ret
        return ret[0]

    def inventoryExists(self, uuid):
        machine = self.getMachineByUUID(uuid)
        if machine:
            return True
        else:
            return False

    def getLastMachineInventoryPart(self, uuid, part):
        if part == 'Network':
            session = create_session()
            query = self.filterOnUUID(session.query(Network).select_from(self.machine.join(self.network)), uuid).all()
            ret = map(lambda a:a.to_a(), query)
            session.close()
        elif part == 'Controller':
            ret = self.getAllDevices(uuid)
        else:
            ret = None
        return ret

    ##################### functions used by querymanager
    def getAllOs(self, ctx, filt = ''):
        """
        @return: all os defined in the GLPI database
        """
        session = create_session()
        query = session.query(OS).select_from(self.os.join(self.machine))
        query = self.__filter_on(query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0))
        query = self.__filter_on_entity(query, ctx)
        if filter != '':
            query = query.filter(self.os.c.name.like('%'+filt+'%'))
        ret = query.all()
        session.close()
        return ret
    def getMachineByOs(self, ctx, osname):
        """
        @return: all machines that have this os
        """
        # TODO use the ctx...
        session = create_session()
        query = session.query(Machine).select_from(self.machine.join(self.os)).filter(self.os.c.name == osname)
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        query = self.__filter_on_entity(query, ctx)
        ret = query.all()
        session.close()
        return ret

    def getAllEntities(self, ctx, filt = ''):
        """
        @return: all entities defined in the GLPI database
        """
        session = create_session()
        query = session.query(Location).select_from(self.model.join(self.machine))
        query = self.__filter_on(query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0))
        query = self.__filter_on_entity(query, ctx)
        if filter != '':
            query = query.filter(self.location.c.name.like('%'+filt+'%'))
        ret = query.all()
        session.close()
        return ret
    def getMachineByEntity(self, ctx, enname):
        """
        @return: all machines that are in this entity
        """
        # TODO use the ctx...
        session = create_session()
        query = session.query(Machine).select_from(self.machine.join(self.location)).filter(self.location.c.name == enname)
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        query = self.__filter_on_entity(query, ctx)
        ret = query.all()
        session.close()
        return ret

    def getEntitiesParentsAsList(self, lids):
        my_parents_ids = []
        my_parents = self.getEntitiesParentsAsDict(lids)
        for p in my_parents:
            for i in my_parents[p]:
                if not my_parents_ids.__contains__(i):
                    my_parents_ids.append(i)
        return my_parents_ids

    def getEntitiesParentsAsDict(self, lids):
        session = create_session()
        if type(lids) != list and type(lids) != tuple:
            lids = (lids)
        query = session.query(Location).all()
        locs = {}
        for l in query:
            locs[l.id] = l.entities_id

        def __getParent(i):
            if locs.has_key(i):
                return locs[i]
            else:
                return None
        ret = {}
        for i in lids:
            t = []
            p = __getParent(i)
            while p != None:
                t.append(p)
                p = __getParent(p)
            ret[i] = t
        return ret

    def getAllVersion4Software(self, ctx, softname, version = ''):
        """
        @return: all softwares defined in the GLPI database
        """
        if not hasattr(ctx, 'locationsid'):
            complete_ctx(ctx)
        session = create_session()
        query = session.query(SoftwareVersion).select_from(self.softwareversions.join(self.software))

        my_parents_ids = self.getEntitiesParentsAsList(ctx.locationsid)
        query = query.filter(or_(self.software.c.entities_id.in_(ctx.locationsid), and_(self.software.c.is_recursive == 1, self.software.c.entities_id.in_(my_parents_ids))))
        r1 = re.compile('\*')
        if r1.search(softname):
            softname = r1.sub('%', softname)
            query = query.filter(self.software.c.name.like(softname))
        else:
            query = query.filter(self.software.c.name == softname)
        if version != '':
            query = query.filter(self.softwareversions.c.name.like('%'+version+'%'))
        ret = query.group_by(self.softwareversions.c.name).all()
        session.close()
        return ret

    def getAllSoftwares(self, ctx, softname = ''):
        """
        @return: all softwares defined in the GLPI database
        """
        if not hasattr(ctx, 'locationsid'):
            complete_ctx(ctx)
        session = create_session()
        query = session.query(Software)
        my_parents_ids = self.getEntitiesParentsAsList(ctx.locationsid)
        query = query.filter(or_(self.software.c.entities_id.in_(ctx.locationsid), and_(self.software.c.is_recursive == 1, self.software.c.entities_id.in_(my_parents_ids))))

        if softname != '':
            query = query.filter(self.software.c.name.like('%'+softname+'%'))
        ret = query.group_by(self.software.c.name).order_by(self.software.c.name).all()
        session.close()
        return ret
    def getMachineBySoftware(self, ctx, swname):
        """
        @return: all machines that have this software
        """
        # TODO use the ctx...
        session = create_session()
        query = session.query(Machine)
        query = query.select_from(self.machine.join(self.inst_software).join(self.softwareversions).join(self.software))
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        query = self.__filter_on_entity(query, ctx)
        if type(swname) == list:
            # FIXME: the way the web interface process dynamic group sub-query
            # is wrong, so for the moment we need this loop:
            while type(swname[0]) == list:
                swname = swname[0]
            query = query.filter(and_(self.software.c.name == swname[0], glpi_license.version == swname[1]))
        else:
            query = query.filter(self.software.c.name == swname).order_by(glpi_license.version)
        ret = query.all()
        session.close()
        return ret
    def getMachineBySoftwareAndVersion(self, ctx, swname):
        return self.getMachineBySoftware(ctx, swname)

    def getAllHostnames(self, ctx, filt = ''):
        """
        @return: all hostnames defined in the GLPI database
        """
        session = create_session()
        query = session.query(Machine)
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        query = self.__filter_on_entity(query, ctx)
        if filter != '':
            query = query.filter(self.machine.c.name.like('%'+filt+'%'))
        ret = query.all()
        session.close()
        return ret
    def getMachineByHostname(self, ctx, hostname):
        """
        @return: all machines that have this hostname
        """
        # TODO use the ctx...
        session = create_session()
        query = session.query(Machine)
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        query = self.__filter_on_entity(query, ctx)
        query = query.filter(self.machine.c.name == hostname)
        ret = query.all()
        session.close()
        return ret

    def getAllContacts(self, ctx, filt = ''):
        """
        @return: all hostnames defined in the GLPI database
        """
        session = create_session()
        query = session.query(Machine)
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        query = self.__filter_on_entity(query, ctx)
        if filter != '':
            query = query.filter(self.machine.c.contact.like('%'+filt+'%'))
        ret = query.group_by(self.machine.c.contact).all()
        session.close()
        return ret
    def getMachineByContact(self, ctx, contact):
        """
        @return: all machines that have this contact
        """
        # TODO use the ctx...
        session = create_session()
        query = session.query(Machine)
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        query = self.__filter_on_entity(query, ctx)
        query = query.filter(self.machine.c.contact == contact)
        ret = query.all()
        session.close()
        return ret

    def getAllContactNums(self, ctx, filt = ''):
        """
        @return: all hostnames defined in the GLPI database
        """
        session = create_session()
        query = session.query(Machine)
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        query = self.__filter_on_entity(query, ctx)
        if filter != '':
            query = query.filter(self.machine.c.contact_num.like('%'+filt+'%'))
        ret = query.group_by(self.machine.c.contact_num).all()
        session.close()
        return ret
    def getMachineByContactNum(self, ctx, contact_num):
        """
        @return: all machines that have this contact number
        """
        # TODO use the ctx...
        session = create_session()
        query = session.query(Machine)
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        query = self.__filter_on_entity(query, ctx)
        query = query.filter(self.machine.c.contact_num == contact_num)
        ret = query.all()
        session.close()
        return ret

    def getAllComments(self, ctx, filt = ''):
        """
        @return: all hostnames defined in the GLPI database
        """
        session = create_session()
        query = session.query(Machine)
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        query = self.__filter_on_entity(query, ctx)
        if filter != '':
            query = query.filter(self.machine.c.comment.like('%'+filt+'%'))
        ret = query.group_by(self.machine.c.comment).all()
        session.close()
        return ret
    def getMachineByComment(self, ctx, comment):
        """
        @return: all machines that have this contact number
        """
        # TODO use the ctx...
        session = create_session()
        query = session.query(Machine)
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        query = self.__filter_on_entity(query, ctx)
        query = query.filter(self.machine.c.comment == comment)
        ret = query.all()
        session.close()
        return ret

    def getAllModels(self, ctx, filt = ''):
        """ @return: all hostnames defined in the GLPI database """
        session = create_session()
        query = session.query(Model).select_from(self.model.join(self.machine))
        query = self.__filter_on(query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0))
        query = self.__filter_on_entity(query, ctx)
        if filter != '':
            query = query.filter(self.model.c.name.like('%'+filt+'%'))
        ret = query.group_by(self.model.c.name).all()
        session.close()
        return ret
    def getMachineByModel(self, ctx, filt):
        """ @return: all machines that have this contact number """
        session = create_session()
        query = session.query(Machine).select_from(self.machine.join(self.model))
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        query = self.__filter_on_entity(query, ctx)
        query = query.filter(self.model.c.name == filt)
        ret = query.all()
        session.close()
        return ret

    def getAllLocations(self, ctx, filt = ''):
        """ @return: all hostnames defined in the GLPI database """
        if not hasattr(ctx, 'locationsid'):
            complete_ctx(ctx)
        session = create_session()
        query = session.query(Locations).select_from(self.locations.join(self.machine))
        query = self.__filter_on(query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0))
        my_parents_ids = self.getEntitiesParentsAsList(ctx.locationsid)
        query = self.__filter_on_entity(query, ctx, my_parents_ids)
        query = query.filter(or_(self.locations.c.entities_id.in_(ctx.locationsid), and_(self.locations.c.is_recursive == 1, self.locations.c.entities_id.in_(my_parents_ids))))
        if filter != '':
            query = query.filter(self.locations.c.completename.like('%'+filt+'%'))
        ret = query.group_by(self.locations.c.completename).all()
        session.close()
        return ret
    def getMachineByLocation(self, ctx, filt):
        """ @return: all machines that have this contact number """
        session = create_session()
        query = session.query(Machine).select_from(self.machine.join(self.locations))
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        query = self.__filter_on_entity(query, ctx)
        query = query.filter(self.locations.c.completename == filt)
        ret = query.all()
        session.close()
        return ret

    def getAllOsSps(self, ctx, filt = ''):
        """ @return: all hostnames defined in the GLPI database """
        session = create_session()
        query = session.query(OsSp).select_from(self.os_sp.join(self.machine))
        query = self.__filter_on(query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0))
        query = self.__filter_on_entity(query, ctx)
        if filter != '':
            query = query.filter(self.os_sp.c.name.like('%'+filt+'%'))
        ret = query.group_by(self.os_sp.c.name).all()
        session.close()
        return ret
    def getMachineByOsSp(self, ctx, filt):
        """ @return: all machines that have this contact number """
        session = create_session()
        query = session.query(Machine).select_from(self.machine.join(self.os_sp))
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        query = self.__filter_on_entity(query, ctx)
        query = query.filter(self.os_sp.c.name == filt)
        ret = query.all()
        session.close()
        return ret

    def getAllGroups(self, ctx, filt = ''):
        """ @return: all hostnames defined in the GLPI database """
        if not hasattr(ctx, 'locationsid'):
            complete_ctx(ctx)
        session = create_session()
        query = session.query(Group).select_from(self.group.join(self.machine))
        query = self.__filter_on(query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0))
        my_parents_ids = self.getEntitiesParentsAsList(ctx.locationsid)
        query = self.__filter_on_entity(query, ctx, my_parents_ids)
        query = query.filter(or_(self.group.c.entities_id.in_(ctx.locationsid), and_(self.group.c.is_recursive == 1, self.group.c.entities_id.in_(my_parents_ids))))
        if filter != '':
            query = query.filter(self.group.c.name.like('%'+filt+'%'))
        ret = query.group_by(self.group.c.name).all()
        session.close()
        return ret
    def getMachineByGroup(self, ctx, filt):# ENTITY!
        """ @return: all machines that have this contact number """
        session = create_session()
        query = session.query(Machine).select_from(self.machine.join(self.group))
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        query = self.__filter_on_entity(query, ctx)
        query = query.filter(self.group.c.entities_id.in_(ctx.locationsid))
        query = query.filter(self.group.c.name == filt)
        ret = query.all()
        session.close()
        return ret

    def getAllNetworks(self, ctx, filt = ''):
        """ @return: all hostnames defined in the GLPI database """
        session = create_session()
        query = session.query(Net).select_from(self.net.join(self.machine))
        query = self.__filter_on(query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0))
        query = self.__filter_on_entity(query, ctx)
        if filter != '':
            query = query.filter(self.net.c.name.like('%'+filt+'%'))
        ret = query.group_by(self.net.c.name).all()
        session.close()
        return ret
    def getMachineByNetwork(self, ctx, filt):
        """ @return: all machines that have this contact number """
        session = create_session()
        query = session.query(Machine).select_from(self.machine.join(self.net))
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = self.__filter_on(query)
        query = self.__filter_on_entity(query, ctx)
        query = query.filter(self.net.c.name == filt)
        ret = query.all()
        session.close()
        return ret

    def getMachineByMacAddress(self, ctx, filt):
        """ @return: all computers that have this mac address """
        session = create_session()
        query = session.query(Machine).select_from(self.machine.join(self.network))
        query = query.filter(self.machine.c.is_deleted == 0).filter(self.machine.c.is_template == 0)
        query = query.filter(and_(self.network.c.itemtype == 'Computer', self.network.c.mac == filt))
        query = self.__filter_on(query)
        if ctx != 'imaging_module':
            query = self.__filter_on_entity(query, ctx)
        ret = query.all()
        session.close()
        return ret

    ##################### for msc
    def getMachinesNetwork(self, uuids):
        """
        return a dict uuid:[macAddress, ipHostNumber, subnetMask, domain]
        """
        session = create_session()
        query = session.query(Network).add_column(self.machine.c.id).add_column(self.domain.c.name).select_from(self.machine.join(self.network).outerjoin(self.domain))
        query = self.filterOnUUID(query.filter(self.network.c.itemtype == 'Computer'), uuids)
        ret = {}
        for n in query.group_by(self.network.c.id).all():
            net = n[0].toH()
            if n[2] != None:
                net['domain'] = n[2]
            else:
                net['domain'] = ''
            uuid = toUUID(n[1])
            if uuid not in ret:
                ret[uuid] = [net]
            else:
                ret[uuid].append(net)
        return ret

    def getMachineNetwork(self, uuid):
        """
        Get a machine network
        """
        session = create_session()
        query = session.query(Network).select_from(self.machine.join(self.network))
        query = self.filterOnUUID(query.filter(self.network.c.itemtype == 'Computer'), uuid)
        ret = unique(map(lambda m: m.toH(), query.all()))
        session.close()
        return ret

    def getMachinesMac(self, uuids):
        """
        Get several machines mac addresses
        """
        session = create_session()
        query = session.query(Network).add_column(self.machine.c.id).select_from(self.machine.join(self.network))
        query = self.filterOnUUID(query.filter(self.network.c.itemtype == 'Computer'), uuids)
        query = query.all()
        session.close()
        ret = {}
        for n, cid in query:
            cuuid = toUUID(cid)
            if not ret.has_key(cuuid):
                ret[cuuid] = []
            if not n.mac in ret[cuuid]:
                ret[cuuid].append(n.mac)
        return ret


    def getMachineMac(self, uuid):
        """
        Get a machine mac addresses
        """
        session = create_session()
        query = session.query(Network).select_from(self.machine.join(self.network))
        query = self.filterOnUUID(query.filter(self.network.c.itemtype == 'Computer'), uuid)
        ret = unique(map(lambda m: m.mac, query.all()))
        session.close()
        return ret

    def orderIpAdresses(self, uuid, hostname, netiface):
        ret_ifmac = []
        ret_ifaddr = []
        ret_netmask = []
        ret_domain = []
        ret_networkUuids = []
        idx_good = 0
        failure = [True, True]
        for iface in netiface:
            if 'ifaddr' in iface and 'gateway' in iface and 'netmask' in iface:
                if iface['gateway'] == None:
                    ret_ifmac.append(iface['ifmac'])
                    ret_ifaddr.append(iface['ifaddr'])
                    ret_netmask.append(iface['netmask'])
                    ret_networkUuids.append(iface['uuid'])
                    if 'domain' in iface:
                        ret_domain.append(iface['domain'])
                    else:
                        ret_domain.append('')
                else:
                    if same_network(iface['ifaddr'], iface['gateway'], iface['netmask']):
                        idx_good += 1
                        ret_ifmac.insert(0, iface['ifmac'])
                        ret_ifaddr.insert(0, iface['ifaddr'])
                        ret_netmask.insert(0, iface['netmask'])
                        ret_networkUuids.insert(0, iface['uuid'])
                        if 'domain' in iface:
                            ret_domain.insert(0, iface['domain'])
                        else:
                            ret_domain.insert(0, '')
                        failure[0] = False
                    else:
                        ret_ifmac.insert(idx_good, iface['ifmac'])
                        ret_ifaddr.insert(idx_good, iface['ifaddr'])
                        ret_netmask.insert(idx_good, iface['netmask'])
                        ret_networkUuids.insert(idx_good, iface['uuid'])
                        if 'domain' in iface:
                            ret_domain.insert(idx_good, iface['domain'])
                        else:
                            ret_domain.insert(idx_good, '')
                        failure[1] = False

        if failure[0]:
            if failure[1]:
                self.logger.warn("Computer %s (uuid:%s) does not have any gateway"%(hostname, uuid))
            else:
                self.logger.warn("Computer %s (uuid:%s) does not have any gateway in it's network"%(hostname, uuid))
        return (ret_ifmac, ret_ifaddr, ret_netmask, ret_domain, ret_networkUuids)

    def getMachineIp(self, uuid):
        """
        Get a machine ip addresses
        """
        # FIXME: should be done on the same model as orderIpAdresses
        session = create_session()
        query = session.query(Network).select_from(self.machine.join(self.network))
        query = self.filterOnUUID(query.filter(self.network.c.itemtype == 'Computer'), uuid)
        ret_gw = []
        ret_nogw = []
        for m in query.all():
            if same_network(m.ip, m.gateway, m.netmask):
                ret_gw.append(m.ip)
            else:
                ret_nogw.append(m.ip)
        ret_gw = unique(ret_gw)
        ret_gw.extend(unique(ret_nogw))

        session.close()
        return ret_gw

    def getIpFromMac(self, mac):
        """
        Get an ip address when a mac address is given
        """
        session = create_session()
        query = session.query(Network).filter(self.network.c.mac == mac)
        ret = query.first().ip
        session.close()
        return ret

    def getIpFromMachine(self, uuid):
        """
        Same as getMachineIp
        TODO: check where it is used
        """
        return self.getMachineIp(uuid)

    def getMachineDomain(self, uuid):
        """
        Get a machine domain name
        """
        session = create_session()
        query = self.filterOnUUID(session.query(Domain).select_from(self.domain.join(self.machine)), uuid)
        ret = query.first()
        if ret != None:
            return ret.name
        else:
            return ''

    def isComputerNameAvailable(self, ctx, locationUUID, name):
        raise Exception("need to be implemented when we would be able to add computers")

# Class for SQLalchemy mapping
class Machine(object):
    def getUUID(self):
        return toUUID(self.id)
    def toH(self):
        return { 'hostname':self.name, 'uuid':toUUID(self.id) }
    def to_a(self):
        return [
            ['name',self.name],
            ['comments',self.comment],
            ['serial',self.serial],
            ['otherserial',self.otherserial],
            ['contact',self.contact],
            ['contact_num',self.contact_num],
            # ['tech_num',self.tech_num],
            ['os',self.operatingsystems_id],
            ['os_version',self.operatingsystemversions_id],
            ['os_sp',self.operatingsystemservicepacks_id],
            ['os_license_number',self.os_license_number],
            ['os_license_id',self.os_licenseid],
            ['location',self.locations_id],
            ['domain',self.domains_id],
            ['network',self.networks_id],
            ['model',self.computermodels_id],
            ['type',self.computertypes_id],
            ['entity',self.entities_id],
            ['uuid',Glpi08().getMachineUUID(self)]
        ]

class Location(object):
    def toH(self):
        return {
            'uuid':toUUID(self.id),
            'name':self.name,
            'completename':self.completename,
            'comments':self.comment,
            'level':self.level
        }

class Processor(object):
    pass

class User(object):
    pass

class Profile(object):
    pass

class UserProfile(object):
    pass

class Network(object):
    def toH(self):
        return {
            'uuid':toUUID(self.id),
            'name': self.name,
            'ifaddr': self.ip,
            'ifmac': self.mac,
            'netmask': self.netmask,
            'gateway': self.gateway,
            'subnet': self.subnet
        }

    def to_a(self):
        return [
            ['uuid', toUUID(self.id)],
            ['name', self.name],
            ['ifaddr', self.ip],
            ['ifmac', self.mac],
            ['netmask', self.netmask],
            ['gateway', self.gateway],
            ['subnet', self.subnet]
        ]

class OS(object):
    pass

class ComputerDevice(object):
    pass

class Domain(object):
    pass

class Software(object):
    pass

class InstSoftware(object):
    pass

class Licenses(object):
    pass

class SoftwareVersion(object):
    pass

class Group(object):
    pass

class OsSp(object):
    pass

class Model(object):
    pass

class Locations(object):
    pass

class Net(object):
    pass


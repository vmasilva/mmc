# -*- coding: utf-8; -*-
#
# (c) 2004-2007 Linbox / Free&ALter Soft, http://linbox.com
# (c) 2007-2009 Mandriva, http://www.mandriva.com/
#
# $Id$
#
# This file is part of Pulse 2, http://pulse2.mandriva.org
#
# Pulse 2 is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Pulse 2 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pulse 2; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

"""
Database class for imaging
"""

from pulse2.database.dyngroup.dyngroup_database_helper import DyngroupDatabaseHelper
from pulse2.database.imaging.types import PULSE2_IMAGING_MENU_ALL, PULSE2_IMAGING_IMAGE_IS_BOTH, PULSE2_IMAGING_IMAGE_IS_IMAGE_ONLY, PULSE2_IMAGING_IMAGE_IS_MASTER_ONLY, PULSE2_IMAGING_MENU_BOOTSERVICE, PULSE2_IMAGING_MENU_IMAGE, PULSE2_IMAGING_TYPE_COMPUTER, PULSE2_IMAGING_TYPE_PROFILE, PULSE2_IMAGING_SYNCHROSTATE_RUNNING, PULSE2_IMAGING_SYNCHROSTATE_TODO, PULSE2_IMAGING_SYNCHROSTATE_DONE, PULSE2_IMAGING_SYNCHROSTATE_INIT_ERROR

from sqlalchemy import create_engine, ForeignKey, Integer, MetaData, Table, Column, and_, or_
from sqlalchemy.orm import create_session, mapper

import logging
import time
import datetime

# THAT REQUIRE TO BE IN A MMC SCOPE, NOT IN A PULSE2 ONE
from pulse2.managers.profile import ComputerProfileManager
from pulse2.managers.location import ComputerLocationManager

DATABASEVERSION = 1

ERR_DEFAULT = 1000
ERR_MISSING_NOMENCLATURE = 1001
ERR_IMAGING_SERVER_DONT_EXISTS = 1003
ERR_ENTITY_ALREADY_EXISTS = 1004
ERR_UNEXISTING_MENUITEM = 1005

class ImagingDatabase(DyngroupDatabaseHelper):
    """
    Class to query the Pulse2 imaging database.

    DyngroupDatabaseHelper is a Singleton, so is ImagingDatabase
    """


    def db_check(self):
        self.my_name = "ImagingDatabase"
        self.configfile = "imaging.ini"
        return DyngroupDatabaseHelper.db_check(self, DATABASEVERSION)

    def activate(self, config):
        self.logger = logging.getLogger()
        DyngroupDatabaseHelper.init(self)
        if self.is_activated:
            self.logger.info("ImagingDatabase don't need activation")
            return None
        self.logger.info("ImagingDatabase is activating")
        self.config = config
        self.db = create_engine(self.makeConnectionPath(), pool_recycle = self.config.dbpoolrecycle, pool_size = self.config.dbpoolsize, convert_unicode=True)
        self.metadata = MetaData(self.db)
        if not self.initMappersCatchException():
            return False
        self.metadata.create_all()
        self.nomenclatures = {'MasteredOnState':MasteredOnState, 'TargetType':TargetType, 'Protocol':Protocol, 'SynchroState':SynchroState}
        self.fk_nomenclatures = {'MasteredOn':{'fk_mastered_on_state':'MasteredOnState'}, 'Target':{'type':'TargetType'}, 'Menu':{'fk_protocol':'Protocol', 'fk_synchrostate':'SynchroState'}}
        self.__loadNomenclatureTables()
        self.loadDefaults()
        self.is_activated = True
        self.dbversion = self.getImagingDatabaseVersion()
        self.logger.debug("ImagingDatabase finish activation")
        return self.db_check()

    def loadDefaults(self):
        self.default_params = {
            'default_name':self.config.web_def_default_menu_name,
            'timeout':self.config.web_def_default_timeout,
            'background_uri':self.config.web_def_default_background_uri,
            'message':self.config.web_def_default_message,
            'protocol':self.config.web_def_default_protocol
        }

    def initMappers(self):
        """
        Initialize all SQLalchemy mappers needed for the imaging database
        """
        self.version = Table("version", self.metadata, autoload = True)

        self.initTables()
        mapper(BootService, self.boot_service)
        mapper(BootServiceInMenu, self.boot_service_in_menu)
        mapper(BootServiceOnImagingServer, self.boot_service_on_imaging_server)
        mapper(Entity, self.entity)
        mapper(Image, self.image)
        mapper(ImageInMenu, self.image_in_menu)
        mapper(ImageOnImagingServer, self.image_on_imaging_server)
        mapper(ImagingServer, self.imaging_server)
        mapper(Internationalization, self.internationalization)
        mapper(Language, self.language)
        mapper(MasteredOn, self.mastered_on)
        mapper(MasteredOnState, self.mastered_on_state)
        mapper(Menu, self.menu) #, properties = { 'default_item':relation(MenuItem), 'default_item_WOL':relation(MenuItem) } )
        mapper(MenuItem, self.menu_item) #, properties = { 'menu' : relation(Menu) })
        mapper(Partition, self.partition)
        mapper(PostInstallScript, self.post_install_script)
        mapper(PostInstallScriptInImage, self.post_install_script_in_image)
        mapper(PostInstallScriptOnImagingServer, self.post_install_script_on_imaging_server)
        mapper(Protocol, self.protocol)
        mapper(SynchroState, self.synchro_state)
        mapper(Target, self.target)
        mapper(TargetType, self.target_type)
        mapper(User, self.user)


    def initTables(self):
        """
        Initialize all SQLalchemy tables
        """

        self.boot_service = Table(
            "BootService",
            self.metadata,
            autoload = True
        )

        self.entity = Table(
            "Entity",
            self.metadata,
            autoload = True
        )

        self.language = Table(
            "Language",
            self.metadata,
            autoload = True
        )

        self.mastered_on_state = Table(
            "MasteredOnState",
            self.metadata,
            autoload = True
        )

        self.synchro_state = Table(
            "SynchroState",
            self.metadata,
            autoload = True
        )

        self.post_install_script = Table(
            "PostInstallScript",
            self.metadata,
            autoload = True
        )

        self.protocol = Table(
            "Protocol",
            self.metadata,
            autoload = True
        )

        self.target_type = Table(
            "TargetType",
            self.metadata,
            autoload = True
        )

        self.user = Table(
            "User",
            self.metadata,
            autoload = True
        )

        self.image = Table(
            "Image",
            self.metadata,
            Column('fk_creator', Integer, ForeignKey('User.id')),
            autoload = True
        )

        self.imaging_server = Table(
            "ImagingServer",
            self.metadata,
            Column('fk_entity', Integer, ForeignKey('Entity.id')),
            autoload = True
        )

        self.internationalization = Table(
            "Internationalization",
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('fk_language', Integer, ForeignKey('Language.id'), primary_key=True),
            useexisting=True,
            autoload = True
        )

        self.menu = Table(
            "Menu",
            self.metadata,
            # cant put them for circular dependancies reasons, the join must be explicit
            # Column('fk_default_item', Integer, ForeignKey('MenuItem.id')),
            Column('fk_default_item', Integer),
            # Column('fk_default_item_WOL', Integer, ForeignKey('MenuItem.id')),
            Column('fk_default_item_WOL', Integer),
            Column('fk_protocol', Integer, ForeignKey('Protocol.id')),
            # fk_name is not an explicit FK, you need to choose the lang before beeing able to join
            Column('fk_synchrostate', Integer, ForeignKey('SynchroState.id')),
            useexisting=True,
            autoload = True
        )

        self.menu_item = Table(
            "MenuItem",
            self.metadata,
            Column('fk_menu', Integer, ForeignKey('Menu.id')),
            # fk_name is not an explicit FK, you need to choose the lang before beeing able to join
            useexisting=True,
            autoload = True
        )

        self.partition = Table(
            "Partition",
            self.metadata,
            Column('fk_image', Integer, ForeignKey('Image.id')),
            useexisting=True,
            autoload = True
        )

        self.boot_service_in_menu = Table(
            "BootServiceInMenu",
            self.metadata,
            Column('fk_bootservice', Integer, ForeignKey('BootService.id'), primary_key=True),
            Column('fk_menuitem', Integer, ForeignKey('MenuItem.id'), primary_key=True),
            useexisting=True,
            autoload = True
        )

        self.boot_service_on_imaging_server = Table(
            "BootServiceOnImagingServer",
            self.metadata,
            Column('fk_boot_service', Integer, ForeignKey('BootService.id'), primary_key=True),
            # Column('fk_imaging_server', Integer, ForeignKey('ImagingServer.id'), primary_key=True),
            # cant declare it implicit as a FK else it make circular dependancies
            Column('fk_imaging_server', Integer, primary_key=True),
            useexisting=True,
            autoload = True
        )

        self.image_in_menu = Table(
            "ImageInMenu",
            self.metadata,
            Column('fk_image', Integer, ForeignKey('Image.id'), primary_key=True),
            Column('fk_menuitem', Integer, ForeignKey('MenuItem.id'), primary_key=True),
            useexisting=True,
            autoload = True
        )

        self.image_on_imaging_server = Table(
            "ImageOnImagingServer",
            self.metadata,
            Column('fk_image', Integer, ForeignKey('Image.id'), primary_key=True),
            Column('fk_imaging_server', Integer, ForeignKey('ImagingServer.id'), primary_key=True),
            useexisting=True,
            autoload = True
        )

        self.target = Table(
            "Target",
            self.metadata,
            Column('fk_entity', Integer, ForeignKey('Entity.id')),
            Column('fk_menu', Integer, ForeignKey('Menu.id')),
            useexisting=True,
            autoload = True
        )

        self.mastered_on = Table(
            "MasteredOn",
            self.metadata,
            Column('fk_mastered_on_state', Integer, ForeignKey('MasteredOnState.id')),
            Column('fk_image', Integer, ForeignKey('Image.id')),
            Column('fk_target', Integer, ForeignKey('Target.id')),
            useexisting=True,
            autoload = True
        )

        self.post_install_script_in_image = Table(
            "PostInstallScriptInImage",
            self.metadata,
            Column('fk_image', Integer, ForeignKey('Image.id'), primary_key=True),
            Column('fk_post_install_script', Integer, ForeignKey('PostInstallScript.id'), primary_key=True),
            useexisting=True,
            autoload = True
        )

        self.post_install_script_on_imaging_server = Table(
            "PostInstallScriptOnImagingServer",
            self.metadata,
            # Column('fk_imaging_server', Integer, ForeignKey('ImagingServer.id'), primary_key=True),
            # circular deps
            Column('fk_imaging_server', Integer, primary_key=True),
            Column('fk_post_install_script', Integer, ForeignKey('PostInstallScript.id'), primary_key=True),
            useexisting=True,
            autoload = True
        )


#self.nomenclatures = {'MasteredOnState':MasteredOnState, 'TargetType':TargetType, 'Protocol':Protocol}
#self.fk_nomenclatures = {'MasteredOn':{'fk_mastered_on_state':'MasteredOnState'}, 'Target':{'type':'TargetType'}, 'Menu':{'fk_protocol':'Protocol'}}

    def __loadNomenclatureTables(self):
        session = create_session()
        for i in self.nomenclatures:
            n = session.query(self.nomenclatures[i]).all()
            self.nomenclatures[i] = {}
            for j in n:
                self.nomenclatures[i][j.id] = j.label
        session.close()

    def completeNomenclatureLabel(self, objs):
        if type(objs) != list and type(objs) != tuple:
            objs = [objs]
        if len(objs) == 0:
            return
        className = str(objs[0].__class__).split("'")[1].split('.')[-1]
        nomenclatures = []
        if self.fk_nomenclatures.has_key(className):
            for i in self.fk_nomenclatures[className]:
                nomenclatures.append([i, i.replace('fk_', ''), self.nomenclatures[self.fk_nomenclatures[className][i]]])
            for obj in objs:
                for fk, field, value in nomenclatures:
                    fk_val = getattr(obj, fk)
                    if fk == field:
                        field = '%s_value'%field
                    if value.has_key(fk_val):
                        setattr(obj, field, value[fk_val])
                    else:
                        self.logger.warn("nomenclature is missing for %s field %s (value = %s)"%(str(obj), field, str(fk_val)))
                        setattr(obj, field, "%s:nomenclature does not exists."%(ERR_MISSING_NOMENCLATURE))


    def completeTarget(self, objs):
        """
        take a list of dict with a fk_target element and add them the target dict that correspond
        """
        ids = {}
        for i in objs:
            ids[i['fk_target']] = None
        ids = ids.keys()
        targets = self.getTargetsById(ids)
        id_target = {}
        for t in targets:
            t = t.toH()
            id_target[t['id']] = t
        for i in objs:
            i['target'] = id_target[i['fk_target']]

    def getImagingDatabaseVersion(self):
        """
        Return the imaging database version.
        We don't use this information for now, but if we can get it this means the database connection is working.

        @rtype: int
        """
        return self.version.select().execute().fetchone()[0]

###########################################################
    def getTargetsEntity(self, uuids):
        session = create_session()
        e = session.query(Entity).add_entity(Target).select_from(self.entity.join(self.target, self.target.c.fk_entity == self.entity.c.id)).filter(self.target.c.uuid.in_(uuids)).all()
        session.close()
        return e

    def getTargetsById(self, ids):
        session = create_session()
        n = session.query(Target).filter(self.target.c.id.in_(ids)).all()
        session.close()
        return n

    def getTargetsByUUID(self, ids):
        session = create_session()
        n = session.query(Target).filter(self.target.c.uuid.in_(ids)).all()
        session.close()
        return n

    def __mergeTargetInMasteredOn(self, mastered_on_list):
        ret = []
        for mastered_on, target in mastered_on_list:
            setattr(mastered_on, 'target', target)
            ret.append(mastered_on)
        return ret

    def __getTargetsMenuQuery(self, session):
        return session.query(Menu).select_from(self.menu.join(self.target))

    def getTargetsMenuTID(self, target_id):
        session = create_session()
        q = self.__getTargetsMenuQuery(session)
        q = q.filter(self.target.c.id == target_id).first() # there should always be only one!
        session.close()
        return q

    def getTargetsMenuTUUID(self, target_id, session = None):
        need_to_close_session = False
        if session == None:
            need_to_close_session = True
            session = create_session()
        q = self.__getTargetsMenuQuery(session)
        q = q.filter(self.target.c.uuid == target_id).first() # there should always be only one!
        if need_to_close_session:
            session.close()
        return q

    def getEntityDefaultMenu(self, loc_id, session = None):
        need_to_close_session = False
        if session == None:
            need_to_close_session = True
            session = create_session()
        q = session.query(Menu).filter(and_(self.entity.c.fk_default_menu == self.menu.c.id, self.entity.c.uuid == loc_id)).first() # there should always be only one!
        if need_to_close_session:
            session.close()
        return q

    def getTargetMenu(self, uuid, type, session = None):
        need_to_close_session = False
        if session == None:
            need_to_close_session = True
            session = create_session()
        q = session.query(Menu).select_from(self.menu.join(self.target)).filter(and_(self.target.c.uuid == uuid, self.target.c.type == type)).first() # there should always be only one!
        if need_to_close_session:
            session.close()
        return q

    def __mergeMenuItemInBootService(self, list_of_bs, list_of_both):
        ret = []
        temporary = {}
        for bs, mi in list_of_both:
            if mi != None:
                temporary[bs.id] = mi
        for bs, bs_id in list_of_bs:
            if temporary.has_key(bs_id):
                setattr(bs, 'menu_item', temporary[bs_id])
            ret.append(bs)
        return ret

    def __mergeBootServiceInMenuItem(self, my_list):
        ret = []
        for mi, bs, menu, bsois in my_list:
            if bs != None:
                setattr(mi, 'boot_service', bs)
            setattr(mi, 'is_local', (bsois != None))
            if menu != None:
                setattr(mi, 'default', (menu.fk_default_item == mi.id))
                setattr(mi, 'default_WOL', (menu.fk_default_item_WOL == mi.id))
            ret.append(mi)
        return ret

    def __mergeMenuItemInImage(self, list_of_im, list_of_both, list_of_target = []):
        ret = []
        temporary = {}
        for im, mi in list_of_both:
            if mi != None:
                temporary[im.id] = mi
        targets = {}
        for t, mo in list_of_target:
            targets[mo.fk_image] = t.uuid
        for im, im_id in list_of_im:
            if temporary.has_key(im_id):
                setattr(im, 'menu_item', temporary[im_id])
            if len(list_of_target) != 0 and targets.has_key(im.id):
                setattr(im, 'mastered_on_target_uuid', targets[im.id])
            ret.append(im)
        return ret

    def __mergeBootServiceOrImageInMenuItem(self, mis):
        """ warning this one does not work on a list but on a tuple of 3 elements (mi, bs, im) """
        (menuitem, bootservice, image, menu) = mis
        if bootservice != None:
            setattr(menuitem, 'boot_service', bootservice)
        if image != None:
            setattr(menuitem, 'image', image)
        if menu != None:
            setattr(menuitem, 'default', (menu.fk_default_item == menuitem.id))
            setattr(menuitem, 'default_WOL', (menu.fk_default_item_WOL == menuitem.id))
        return menuitem

    def __mergeImageInMenuItem(self, my_list):
        ret = []
        for mi, im, menu in my_list:
            if im != None:
                setattr(mi, 'image', im)
            if menu != None:
                setattr(mi, 'default', (menu.fk_default_item == mi.id))
                setattr(mi, 'default_WOL', (menu.fk_default_item_WOL == mi.id))
            ret.append(mi)
        return ret

    def __getMenusImagingServer(self, session, menu_id):
        imaging_server = session.query(ImagingServer).select_from(self.imaging_server.outerjoin(self.entity).outerjoin(self.target)).filter(or_(self.entity.c.fk_default_menu == menu_id, self.target.c.fk_menu == menu_id)).first()
        if imaging_server:
            return imaging_server
        else:
            self.logger.error("cant find any imaging_server for menu '%s'"%(menu_id))
            return  None

    def getMenuContent(self, menu_id, type = PULSE2_IMAGING_MENU_ALL, start = 0, end = -1, filter = '', session = None):# TODO implement the start/end with a union betwen q1 and q2
        session_need_close = False
        if session == None:
            session = create_session()
            session_need_close = True

        mi_ids = session.query(MenuItem).add_column(self.menu_item.c.id).select_from(self.menu_item.join(self.menu, self.menu_item.c.fk_menu == self.menu.c.id))
        if filter != '':
            mi_ids = mi_ids.filter(and_(self.menu.c.id == menu_id, self.menu_item.c.desc.like('%'+filter+'%')))
        else:
            mi_ids = mi_ids.filter(self.menu.c.id == menu_id)
        mi_ids = mi_ids.order_by(self.menu_item.c.order)
        if end != -1:
            mi_ids = mi_ids.offset(int(start)).limit(int(end)-int(start))
        else:
            mi_ids = mi_ids.all()
        mi_ids = map(lambda x:x[1], mi_ids)

        imaging_server = self.__getMenusImagingServer(session, menu_id)
        is_id = 0
        if imaging_server:
            is_id = imaging_server.id

        q = []
        if type == PULSE2_IMAGING_MENU_ALL or type == PULSE2_IMAGING_MENU_BOOTSERVICE:
            q1 = session.query(MenuItem).add_entity(BootService).add_entity(Menu).add_entity(BootServiceOnImagingServer)
            q1 = q1.select_from(self.menu_item.join(self.boot_service_in_menu).join(self.boot_service).join(self.menu, self.menu_item.c.fk_menu == self.menu.c.id).outerjoin(self.boot_service_on_imaging_server))
            q1 = q1.filter(and_(self.menu_item.c.id.in_(mi_ids), or_(self.boot_service_on_imaging_server.c.fk_boot_service == None, self.boot_service_on_imaging_server.c.fk_imaging_server == is_id)))
            q1 = q1.order_by(self.menu_item.c.order).all()
            q1 = self.__mergeBootServiceInMenuItem(q1)
            q.extend(q1)
        if type == PULSE2_IMAGING_MENU_ALL or type == PULSE2_IMAGING_MENU_IMAGE:
            q2 = session.query(MenuItem).add_entity(Image).add_entity(Menu).select_from(self.menu_item.join(self.image_in_menu).join(self.image).join(self.menu, self.menu_item.c.fk_menu == self.menu.c.id))
            q2 = q2.filter(self.menu_item.c.id.in_(mi_ids)).order_by(self.menu_item.c.order).all()
            q2 = self.__mergeImageInMenuItem(q2)
            q.extend(q2)
        if session_need_close:
            session.close()
        q.sort(lambda x,y: cmp(x.order, y.order))
        return q

    def getLastMenuItemOrder(self, menu_id):
        session = create_session()
        q = session.query(MenuItem).filter(self.menu_item.c.fk_menu == menu_id).max(self.menu_item.c.order)
        session.close()
        if q == None:
            return 0
        return q

    def countMenuContentFast(self, menu_id): # get PULSE2_IMAGING_MENU_ALL and empty filter
        session = create_session()
        q = session.query(MenuItem).filter(self.menu_item.c.fk_menu == menu_id).count()
        session.close()
        return q
    def countMenuContent(self, menu_id, type = PULSE2_IMAGING_MENU_ALL, filter = ''):
        if type == PULSE2_IMAGING_MENU_ALL and filter =='':
            return self.countMenuContentFast(menu_id)

        session = create_session()
        q = 0
        if type == PULSE2_IMAGING_MENU_ALL or type == PULSE2_IMAGING_MENU_BOOTSERVICE:
            q1 = session.query(MenuItem).add_entity(BootService).select_from(self.menu_item.join(self.boot_service_in_menu).join(self.boot_service))
            q1 = q1.filter(and_(self.menu_item.c.fk_menu == menu_id, self.boot_service.c.desc.like('%'+filter+'%'))).count()
            q += q1
        if type == PULSE2_IMAGING_MENU_ALL or type == PULSE2_IMAGING_MENU_IMAGE:
            q2 = session.query(MenuItem).add_entity(Image).select_from(self.menu_item.join(self.image_in_menu).join(self.image))
            q2 = q2.filter(and_(self.menu_item.c.fk_menu == menu_id, self.boot_service.c.desc.like('%'+filter+'%'))).count()
            q += q2
        session.close()
        return q

###########################################################
    def getEntityUrl(self, location_uuid):
        session = create_session()
        # there should be just one imaging server per entity
        q = session.query(ImagingServer).select_from(self.imaging_server.join(self.entity)).filter(self.entity.c.uuid == location_uuid).first()
        session.close()
        if q == None:
            return None
        return q.url

    def __MasteredOns4Location(self, session, location_uuid, filter):
        n = session.query(MasteredOn).add_entity(Target).select_from(self.mastered_on.join(self.target).join(self.entity)).filter(self.entity.c.uuid == location_uuid)
        if filter != '':
            n = n.filter(or_(self.mastered_on.c.title.like('%'+filter+'%'), self.target.c.name.like('%'+filter+'%')))
        return n

    def getMasteredOns4Location(self, location_uuid, start, end, filter):
        session = create_session()
        n = self.__MasteredOns4Location(session, location_uuid, filter)
        if end != -1:
            n = n.offset(int(start)).limit(int(end)-int(start))
        else:
            n = n.all()
        session.close()
        n = self.__mergeTargetInMasteredOn(n)
        return n

    def countMasteredOns4Location(self, location_uuid, filter):
        session = create_session()
        n = self.__MasteredOns4Location(session, location_uuid, filter)
        n = n.count()
        session.close()
        return n

    #####################
    def __MasteredOnsOnTargetByIdAndType(self, session, target_id, type, filter):
        q = session.query(MasteredOn).add_entity(Target).select_from(self.mastered_on.join(self.target)).filter(self.target.c.uuid == target_id)
        if type == PULSE2_IMAGING_TYPE_COMPUTER:
            q = q.filter(self.target.c.type == 1)
        elif type == PULSE2_IMAGING_TYPE_PROFILE:
            q = q.filter(self.target.c.type == 2)
        else:
            self.logger.error("type %s does not exists!"%(type))
            # to be sure we dont get anything, this is an error case!
            q = q.filter(self.target.c.type == 0)
        if filter != '':
            q = q.filter(or_(self.mastered_on.c.title.like('%'+filter+'%'), self.target.c.name.like('%'+filter+'%')))
        return q

    def getMasteredOnsOnTargetByIdAndType(self, target_id, type, start, end, filter):
        session = create_session()
        q = self.__MasteredOnsOnTargetByIdAndType(session, target_id, type, filter)
        if end != -1:
            q = q.offset(int(start)).limit(int(end)-int(start))
        else:
            q = q.all()
        session.close()
        q = self.__mergeTargetInMasteredOn(q)
        return q

    def countMasteredOnsOnTargetByIdAndType(self, target_id, type, filter):
        session = create_session()
        q = self.__MasteredOnsOnTargetByIdAndType(session, target_id, type, filter)
        q = q.count()
        session.close()
        return q

    ######################
    def __PossibleBootServices(self, session, target_uuid, filter):
        q = session.query(BootService).add_column(self.boot_service.c.id)
        q = q.select_from(self.boot_service \
                .outerjoin(self.boot_service_on_imaging_server, self.boot_service.c.id == self.boot_service_on_imaging_server.c.fk_boot_service) \
                .outerjoin(self.imaging_server, self.imaging_server.c.id == self.boot_service_on_imaging_server.c.fk_imaging_server) \
                .outerjoin(self.entity).outerjoin(self.target))
        q = q.filter(or_(self.target.c.uuid == target_uuid, self.boot_service_on_imaging_server.c.fk_boot_service == None))
        if filter != '':
            q = q.filter(or_(self.boot_service.c.desc.like('%'+filter+'%'), self.boot_service.c.value.like('%'+filter+'%')))
        return q

    def __EntityBootServices(self, session, loc_id, filter):
        q = session.query(BootService).add_column(self.boot_service.c.id)
        q = q.select_from(self.boot_service \
                .outerjoin(self.boot_service_on_imaging_server, self.boot_service.c.id == self.boot_service_on_imaging_server.c.fk_boot_service) \
                .outerjoin(self.imaging_server, self.imaging_server.c.id == self.boot_service_on_imaging_server.c.fk_imaging_server) \
                .outerjoin(self.entity))
        q = q.filter(or_(self.entity.c.uuid == loc_id, self.boot_service_on_imaging_server.c.fk_boot_service == None))
        if filter != '':
            q = q.filter(or_(self.boot_service.c.desc.like('%'+filter+'%'), self.boot_service.c.value.like('%'+filter+'%')))
        return q

    def __PossibleBootServiceAndMenuItem(self, session, bs_ids, menu_id):
        q = session.query(BootService).add_entity(MenuItem)
        q = q.filter(and_(
            self.boot_service_in_menu.c.fk_bootservice == self.boot_service.c.id,
            self.boot_service_in_menu.c.fk_menuitem == self.menu_item.c.id,
            self.menu_item.c.fk_menu == menu_id,
            self.boot_service.c.id.in_(bs_ids)
        )).all()
        return q

    def getPossibleBootServices(self, target_uuid, start, end, filter):
        session = create_session()
        menu = self.getTargetsMenuTUUID(target_uuid)
        q1 = self.__PossibleBootServices(session, target_uuid, filter)
        q1 = q1.group_by(self.boot_service.c.id)
        if end != -1:
            q1 = q1.offset(int(start)).limit(int(end)-int(start))
        else:
            q1 = q1.all()
        bs_ids = map(lambda bs:bs[1], q1)
        q2 = self.__PossibleBootServiceAndMenuItem(session, bs_ids, menu.id)
        session.close()

        q = self.__mergeMenuItemInBootService(q1, q2)
        return q

    def getEntityBootServices(self, loc_id, start, end, filter):
        session = create_session()
        menu = self.getEntityDefaultMenu(loc_id)
        q1 = self.__EntityBootServices(session, loc_id, filter)
        q1 = q1.group_by(self.boot_service.c.id)
        if end != -1:
            q1 = q1.offset(int(start)).limit(int(end)-int(start))
        else:
            q1 = q1.all()
        bs_ids = map(lambda bs:bs[1], q1)
        q2 = self.__PossibleBootServiceAndMenuItem(session, bs_ids, menu.id)
        session.close()

        q = self.__mergeMenuItemInBootService(q1, q2)
        return q

    def countPossibleBootServices(self, target_uuid, filter):
        session = create_session()
        q = self.__PossibleBootServices(session, target_uuid, filter)
        q = q.count()
        session.close()
        return q

    def countEntityBootServices(self, loc_id, filter):
        session = create_session()
        q = self.__EntityBootServices(session, loc_id, filter)
        q = q.count()
        session.close()
        return q

    def __createNewMenuItem(self, session, menu_id, params):
        mi = MenuItem()
        params['order'] = self.getLastMenuItemOrder(menu_id) + 1
        mi = self.__fillMenuItem(session, mi, menu_id, params)
        return mi

    def __fillMenuItem(self, session, mi, menu_id, params):
        if params.has_key('hidden'):
            mi.hidden = params['hidden']
        else:
            mi.hidden = True
        if params.has_key('hidden_WOL'):
            mi.hidden_WOL = params['hidden_WOL']
        else:
            mi.hidden_WOL = True
        if params.has_key('order'):
            mi.order = params['order']
        mi.fk_menu = menu_id
        session.save_or_update(mi)
        return mi

    ERR_TARGET_HAS_NO_MENU = 1000
    ERR_ENTITY_HAS_NO_DEFAULT_MENU = 1002
    def __addMenuDefaults(self, session, menu, mi, params):
        is_menu_modified = False
        if params.has_key('default') and params['default']:
            is_menu_modified = True
            menu.fk_default_item = mi.id
        if params.has_key('default_WOL') and params['default_WOL']:
            is_menu_modified = True
            menu.fk_default_item_WOL = mi.id
        if is_menu_modified:
            session.save_or_update(menu)
        return menu

    def __editMenuDefaults(self, session, menu, mi, params):
        is_menu_modified = False
        if type(menu) in (long, int):
            menu = session.query(Menu).filter(self.menu.c.id == menu).first()
        if menu.fk_default_item != mi.id and params['default']:
            is_menu_modified = True
            menu.fk_default_item = mi.id
        if menu.fk_default_item == mi.id and not params['default']:
            is_menu_modified = True
            menu.fk_default_item = None

        if menu.fk_default_item_WOL != mi.id and params['default_WOL']:
            is_menu_modified = True
            menu.fk_default_item_WOL = mi.id
        if menu.fk_default_item_WOL == mi.id and not params['default_WOL']:
            is_menu_modified = True
            menu.fk_default_item_WOL = None

        if is_menu_modified:
            session.save_or_update(menu)
        return menu

    def __addBootServiceInMenu(self, session, mi_id, bs_uuid):
        bsim = BootServiceInMenu()
        bsim.fk_menuitem = mi_id
        bsim.fk_bootservice = uuid2id(bs_uuid)
        session.save(bsim)
        session.flush()
        return bsim

    def __addImageInMenu(self, session, mi_id, im_uuid):
        imim = ImageInMenu()
        imim.fk_menuitem = mi_id
        imim.fk_image = uuid2id(im_uuid)
        session.save(imim)
        session.flush()
        return imim

    def __addService(self, session, bs_uuid, menu, params):
        bs = session.query(BootService).filter(self.boot_service.c.id == uuid2id(bs_uuid)).first()
        # TODO : what do we do with bs ?
        if menu == None:
            raise '%s:Please create menu before trying to put a bootservice' % (self.ERR_TARGET_HAS_NO_MENU)

        mi = self.__createNewMenuItem(session, menu.id, params)
        session.flush()

        self.__addMenuDefaults(session, menu, mi, params)
        self.__addBootServiceInMenu(session, mi.id, bs_uuid)

        session.close()
        return None

    def addServiceToTarget(self, bs_uuid, target_uuid, params):
        session = create_session()
        menu = self.getTargetsMenuTUUID(target_uuid, session)
        ret = self.__addService(session, bs_uuid, menu, params)
        session.close()
        return ret

    def addServiceToEntity(self, bs_uuid, loc_id, params):
        session = create_session()
        menu = self.getEntityDefaultMenu(loc_id, session)
        ret = self.__addService(session, bs_uuid, menu, params)
        session.close()
        return ret

    def __getServiceMenuItem(self, session, bs_uuid, target_uuid):
        mi = session.query(MenuItem).select_from(self.menu_item.join(self.boot_service_in_menu).join(self.boot_service).join(self.menu).join(self.target))
        mi = mi.filter(and_(self.boot_service.c.id == uuid2id(bs_uuid), self.target.c.uuid == target_uuid)).first()
        return mi

    def __editService(self, session, bs_uuid, menu, mi, params):
        bs = session.query(BootService).filter(self.boot_service.c.id == uuid2id(bs_uuid)).first();
        # TODO : what do we do with bs ?
        if menu == None:
            raise '%s:Please create menu before trying to put a bootservice' % (self.ERR_TARGET_HAS_NO_MENU)

        mi = self.__fillMenuItem(session, mi, menu.id, params)
        session.flush()

        self.__editMenuDefaults(session, menu, mi, params)

        session.flush()
        return None

    def editServiceToTarget(self, bs_uuid, target_uuid, params):
        session = create_session()
        menu = self.getTargetsMenuTUUID(target_uuid, session)
        mi = self.__getServiceMenuItem(session, bs_uuid, target_uuid)
        ret = self.__editService(session, bs_uuid, menu, mi, params)
        session.close()
        return ret

    def __getMenuItemByUUID(self, session, mi_uuid):
        return session.query(MenuItem).filter(self.menu_item.c.id == uuid2id(mi_uuid)).first()

    def editServiceToEntity(self, mi_uuid, loc_id, params):
        session = create_session()
        if self.isLocalBootService(mi_uuid, session):
            # we can change the title/desc/...
            bs = session.query(BootService).select_form(self.boot_service.join(self.boot_service_in_menu))
            bs = bs.filter(self.boot_service_in_menu.c.fk_menuitem == uuid2id(mi_uuid)).first()
            if bs.default_name != params['default_name']:
                bs.default_name = params['default_name']
                session.save_or_update(bs)
        mi = self.__getMenuItemByUUID(session, mi_uuid)
        if mi == None:
            raise '%s:This MenuItem doesnot exists'%(ERR_UNEXISTING_MENUITEM)
        ret = self.__fillMenuItem(session, mi, mi.fk_menu, params)
        # TODO : what do we do with ret ?
        session.flush()
        self.__editMenuDefaults(session, mi.fk_menu, mi, params)
        session.flush()
        session.close()
        return None

    def delServiceToTarget(self, bs_uuid, target_uuid):
        session = create_session()
        mi = session.query(MenuItem).select_from(self.menu_item.join(self.boot_service_in_menu).join(self.boot_service).join(self.menu).join(self.target))
        mi = mi.filter(and_(self.boot_service.c.id == uuid2id(bs_uuid), self.target.c.uuid == target_uuid)).first()
        bsim = session.query(BootServiceInMenu).select_from(self.boot_service_in_menu.join(self.menu_item).join(self.boot_service).join(self.menu).join(self.target))
        bsim = bsim.filter(and_(self.boot_service.c.id == uuid2id(bs_uuid), self.target.c.uuid == target_uuid)).first()
        session.delete(mi)
        session.delete(bsim)
        session.flush()

        session.close()
        return None

    def delServiceToEntity(self, bs_uuid, loc_id):
        session = create_session()
        mi = session.query(MenuItem).select_from(self.menu_item.join(self.boot_service_in_menu).join(self.boot_service).join(self.menu))
        mi = mi.filter(and_(self.boot_service.c.id == uuid2id(bs_uuid), self.menu.c.id == self.entity.c.fk_default_menu, self.entity.c.uuid == loc_id)).first()
        bsim = session.query(BootServiceInMenu).select_from(self.boot_service_in_menu.join(self.menu_item).join(self.boot_service).join(self.menu))
        bsim = bsim.filter(and_(self.boot_service.c.id == uuid2id(bs_uuid), self.menu.c.id == self.entity.c.fk_default_menu, self.entity.c.uuid == loc_id)).first()
        session.delete(mi)
        session.delete(bsim)
        session.flush()

        session.close()
        return None

    def getMenuItemByUUID(self, mi_uuid, session = None):
        session_need_close = False
        if session == None:
            session_need_close = True
            session = create_session()
        mi = session.query(MenuItem).add_entity(BootService).add_entity(Image).add_entity(Menu)
        mi = mi.select_from(self.menu_item.join(self.menu, self.menu.c.id == self.menu_item.c.fk_menu).outerjoin(self.boot_service_in_menu).outerjoin(self.boot_service).outerjoin(self.image_in_menu).outerjoin(self.image))
        mi = mi.filter(self.menu_item.c.id == uuid2id(mi_uuid)).first()
        mi = self.__mergeBootServiceOrImageInMenuItem(mi)
        if hasattr(mi, 'boot_service'):
            local = self.isLocalBootService(mi_uuid, session)
            setattr(mi.boot_service, 'is_local', local)
        if session_need_close:
            session.close()
        return mi

    ######################
    def __PossibleImages(self, session, target_uuid, is_master, filter):
        q = session.query(Image).add_column(self.image.c.id)
        q = q.select_from(self.image.join(self.image_on_imaging_server).join(self.imaging_server).join(self.entity).join(self.target, self.target.c.fk_entity == self.entity.c.id).join(self.mastered_on, self.mastered_on.c.fk_image == self.image.c.id))
        q = q.filter(self.target.c.uuid == target_uuid) # , or_(self.image.c.is_master == True, and_(self.image.c.is_master == False, )))
        if filter != '':
            q = q.filter(or_(self.image.c.desc.like('%'+filter+'%'), self.image.c.value.like('%'+filter+'%')))
        if is_master == PULSE2_IMAGING_IMAGE_IS_MASTER_ONLY:
            q = q.filter(self.image.c.is_master == True)
        elif is_master == PULSE2_IMAGING_IMAGE_IS_IMAGE_ONLY:
            q = q.filter(and_(self.image.c.is_master == False, self.target.c.id == self.mastered_on.c.fk_target))
        elif is_master == PULSE2_IMAGING_IMAGE_IS_BOTH:
            pass

        return q

    def __EntityImages(self, session, loc_id, filter):
        q = session.query(Image).add_column(self.image.c.id)
        q = q.select_from(self.image.join(self.image_on_imaging_server).join(self.imaging_server).join(self.entity))
        q = q.filter(and_(self.entity.c.uuid == loc_id, self.image.c.is_master == True))
        return q

    def __PossibleImageAndMenuItem(self, session, bs_ids, menu_id):
        q = session.query(Image).add_entity(MenuItem)
        q = q.filter(and_(
            self.image_in_menu.c.fk_image == self.image.c.id,
            self.image_in_menu.c.fk_menuitem == self.menu_item.c.id,
            self.menu_item.c.fk_menu == menu_id,
            self.image.c.id.in_(bs_ids)
        )).all()
        return q

    def getPossibleImagesOrMaster(self, target_uuid, is_master, start, end, filter):
        session = create_session()
        menu = self.getTargetsMenuTUUID(target_uuid)
        q1 = self.__PossibleImages(session, target_uuid, is_master, filter)
        q1 = q1.group_by(self.image.c.id)
        if end != -1:
            q1 = q1.offset(int(start)).limit(int(end)-int(start))
        else:
            q1 = q1.all()
        bs_ids = map(lambda bs:bs[1], q1)
        q2 = self.__PossibleImageAndMenuItem(session, bs_ids, menu.id)

        im_ids = map(lambda im:im[0].id, q1)
        q3 = session.query(Target).add_entity(MasteredOn).select_from(self.target.join(self.mastered_on)).filter(self.mastered_on.c.fk_image.in_(im_ids)).all()
        session.close()

        q = self.__mergeMenuItemInImage(q1, q2, q3)
        return q

    def countPossibleImagesOrMaster(self, target_uuid, type, filter):
        session = create_session()
        q = self.__PossibleImages(session, target_uuid, type, filter)
        q = q.count()
        session.close()
        return q

    def getPossibleImages(self, target_uuid, start, end, filter):
        return self.getPossibleImagesOrMaster(target_uuid, PULSE2_IMAGING_IMAGE_IS_IMAGE_ONLY, start, end, filter)

    def getPossibleMasters(self, target_uuid, start, end, filter):
        return self.getPossibleImagesOrMaster(target_uuid, PULSE2_IMAGING_IMAGE_IS_MASTER_ONLY, start, end, filter)

    def getEntityMasters(self, loc_id, start, end, filter):
        session = create_session()
        menu = self.getEntityDefaultMenu(loc_id)
        if menu == None:
            raise "%s:Entity does not have a default menu" % (self.ERR_ENTITY_HAS_NO_DEFAULT_MENU)
        q1 = self.__EntityImages(session, loc_id, filter)
        q1 = q1.group_by(self.image.c.id)
        if end != -1:
            q1 = q1.offset(int(start)).limit(int(end)-int(start))
        else:
            q1 = q1.all()
        bs_ids = map(lambda bs:bs[1], q1)
        q2 = self.__PossibleImageAndMenuItem(session, bs_ids, menu.id)
        session.close()

        q = self.__mergeMenuItemInImage(q1, q2)
        return q

    def countPossibleImages(self, target_uuid, filter):
        return self.countPossibleImagesOrMaster(target_uuid, PULSE2_IMAGING_IMAGE_IS_IMAGE_ONLY, filter)

    def countPossibleMasters(self, target_uuid, filter):
        return self.countPossibleImagesOrMaster(target_uuid, PULSE2_IMAGING_IMAGE_IS_MASTER_ONLY, filter)

    def countEntityMasters(self, loc_id, filter):
        session = create_session()
        q = self.__EntityImages(session, loc_id, filter)
        q = q.count()
        session.close()
        return q

    def __addImage(self, session, item_uuid, menu, params):
        im = session.query(Image).filter(self.image.c.id == uuid2id(item_uuid)).first();
        # TODO : what do we do with im ?
        if menu == None:
            raise '%s:Please create menu before trying to put an image' % (self.ERR_TARGET_HAS_NO_MENU)

        if params.has_key('name') and not params.has_key('default_name'):
            params['default_name'] = params['name']
        mi = self.__createNewMenuItem(session, menu.id, params)
        session.flush()

        self.__addMenuDefaults(session, menu, mi, params)
        self.__addImageInMenu(session, mi.id, item_uuid)

        session.close()
        return None

    def addImageToTarget(self, item_uuid, target_uuid, params):
        session = create_session()
        menu = self.getTargetsMenuTUUID(target_uuid, session)
        ret = self.__addImage(session, item_uuid, menu, params)
        session.close()
        return ret

    def registerImage(self, imaging_server_uuid, computer_uuid, params):
        """
        Registers an image into the database, and link it to a package server
        and to a computer.

        @return: True on success, else will raise an exception
        @rtype: bool
        """
        session = create_session()
        # create the image item
        image = Image()
        image.name = params['name']
        image.desc = params['desc']
        image.path = params['path']
        image.uuid = params['uuid']
        image.checksum = params['checksum']
        image.size = params['size']
        image.creation_date = datetime.date.fromtimestamp(time.mktime(params['creation_date']))
        image.fk_creator = 1 # TOBEDONE image['']
        image.is_master = params['is_master']
        session.save(image)
        session.flush()

        # fill the mastered_on
        #   there is way to much fields!
        mastered_on = MasteredOn()
        mastered_on.timestamp = datetime.date.fromtimestamp(time.mktime(params['creation_date']))
        mastered_on.title = params['name']
        mastered_on.detail = params['desc']
        mastered_on.fk_mastered_on_state = 1 # done
        mastered_on.fk_image = image.id
        target = session.query(Target).filter(self.target.c.uuid == computer_uuid).first()
        mastered_on.fk_target = target.id
        session.save(mastered_on)

        # link the image to the imaging_server
        ims = session.query(ImagingServer).filter(self.imaging_server.c.packageserver_uuid == imaging_server_uuid).first()
        ioims = ImageOnImagingServer()
        ioims.fk_image = image.id
        ioims.fk_imaging_server = ims.id
        session.save(ioims)

        # link the image to the machine
        # DONT PUT IN THE MENU BY DEFAULT
        # self.addImageToTarget(id2uuid(image.id), computer_uuid, params)
        session.flush()
        session.close()
        return True

    def addImageToEntity(self, item_uuid, loc_id, params):
        session = create_session()
        menu = self.getEntityDefaultMenu(loc_id, session)
        ret = self.__addImage(session, item_uuid, menu, params)
        session.close()
        return ret

    def __editImage(self, session, item_uuid, menu, mi, params):
        im = session.query(Image).filter(self.image.c.id == uuid2id(item_uuid)).first();
        # TODO : what do we do with im ?
        if menu == None:
            raise '%s:Please create menu before trying to put an image' % (self.ERR_TARGET_HAS_NO_MENU)

        mi = self.__fillMenuItem(session, mi, menu.id, params)
        session.flush()

        self.__editMenuDefaults(session, menu, mi, params)

        session.flush()
        return None

    def __getImageMenuItem(self, session, item_uuid, target_uuid):
        mi = session.query(MenuItem).select_from(self.menu_item.join(self.image_in_menu).join(self.image).join(self.menu).join(self.target))
        mi = mi.filter(and_(self.image.c.id == uuid2id(item_uuid), self.target.c.uuid == target_uuid)).first()
        return mi

    def __getImageMenuItem4Entity(self, session, item_uuid, loc_id):
        mi = session.query(MenuItem).select_from(self.menu_item.join(self.image_in_menu).join(self.image).join(self.menu))
        mi = mi.filter(and_(self.image.c.id == uuid2id(item_uuid), self.menu.c.id == self.entity.c.fk_default_menu, self.entity.c.uuid == loc_id)).first()
        return mi

    def editImageToTarget(self, item_uuid, target_uuid, params):
        session = create_session()
        menu = self.getTargetsMenuTUUID(target_uuid, session)
        mi = self.__getImageMenuItem(session, item_uuid, target_uuid)
        ret = self.__editImage(session, item_uuid, menu, mi, params)
        session.close()
        return ret

    def editImageToEntity(self, item_uuid, loc_id, params):
        session = create_session()
        menu = self.getEntityDefaultMenu(loc_id, session)
        mi = self.__getImageMenuItem4Entity(session, item_uuid, loc_id)
        ret = self.__editImage(session, item_uuid, menu, mi, params)
        session.close()
        return ret

    def editImage(self, item_uuid, target_uuid, params):
        session = create_session()
        im = session.query(Image).filter(self.image.c.id == uuid2id(item_uuid)).first()
        if im == None:
            raise "%s:Cant find the image you are trying to edit."%(ERR_DEFAULT)
        need_to_be_save = False
        for p in ('name', 'desc', 'is_master'):
            if params.has_key(p) and params[p] != getattr(im, p):
                need_to_be_save = True
                setattr(im, p, params[p])

        if params.has_key('is_master'):
            # there should only be one...
            if params['is_master'] and params.has_key('post_install_script') or not params['is_master']:
                pisiis = session.query(PostInstallScriptInImage).filter(self.post_install_script_in_image.c.fk_image == uuid2id(item_uuid)).all()
                for p in pisiis:
                    session.delete(p)

            if params['is_master'] and params.has_key('post_install_script'):
                pisii = PostInstallScriptInImage()
                pisii.fk_image = uuid2id(item_uuid)
                pisii.fk_post_install_script = uuid2id(params['post_install_script'])
                session.save(pisii)

        if need_to_be_save:
            session.save_or_update(im)
        session.flush()
        session.close()
        return im.id

    def delImageToTarget(self, item_uuid, target_uuid):
        session = create_session()
        mi = session.query(MenuItem).select_from(self.menu_item.join(self.image_in_menu).join(self.image).join(self.menu).join(self.target))
        mi = mi.filter(and_(self.image.c.id == uuid2id(item_uuid), self.target.c.uuid == target_uuid)).first()
        iim = session.query(ImageInMenu).select_from(self.image_in_menu.join(self.menu_item).join(self.image).join(self.menu).join(self.target))
        iim = iim.filter(and_(self.image.c.id == uuid2id(item_uuid), self.target.c.uuid == target_uuid)).first()
        session.delete(mi)
        session.delete(iim)
        # TODO when it's not a master and the computer is the only one, what should we do with the image?
        session.flush()

        session.close()
        return None

    ######################
    def __TargetImagesQuery(self, session, target_uuid, type, filter):
        q = session.query(Image).add_entity(MenuItem)
        q = q.select_from(self.image.join(self.image_on_imaging_server).join(self.imaging_server).join(self.entity).join(self.target).join(self.image_in_menu).join(self.menu_item))
        q = q.filter(and_(self.target.c.uuid == target_uuid, or_(self.image.c.desc.like('%'+filter+'%'), self.image.c.value.like('%'+filter+'%'))))
        return q

    def __TargetImagesNoMaster(self, session, target_uuid, type, filter):
        q = self.__TargetImagesQuery(session, target_uuid, type, filter)
        q.filter(self.image.c.is_master == False)
        return q

    def __TargetImagesIsMaster(self, session, target_uuid, type, filter):
        q = self.__TargetImagesQuery(session, target_uuid, type, filter)
        q.filter(self.image.c.is_master == True)
        return q

    ##
    def __ImagesInEntityQuery(self, session, entity_uuid, filter):
        q = session.query(Image).add_entity(MenuItem)
        q = q.select_from(self.image.join(self.image_on_imaging_server).join(self.imaging_server).join(self.entity).outerjoin(self.image_in_menu).outerjoin(self.menu_item))
        q = q.filter(and_(self.entity.c.uuid == entity_uuid, or_(self.image.c.desc.like('%'+filter+'%'), self.image.c.value.like('%'+filter+'%'))))
        return q

    def __ImagesInEntityNoMaster(self, session, target_uuid, type, filter):
        q = self.__ImagesInEntityQuery(session, target_uuid, type, filter)
        q.filter(self.image.c.is_master == False)
        return q

    def __ImagesInEntityIsMaster(self, session, target_uuid, type, filter):
        q = self.__ImagesInEntityQuery(session, target_uuid, type, filter)
        q.filter(self.image.c.is_master == False)
        return q

    def getTargetImages(self, target_id, type, start, end, filter):
        pass

    def countTargetImages(self, target_id, type, filter):
        pass

    ######################
    def getBootServicesOnTargetById(self, target_id, start, end, filter):
        menu = self.getTargetsMenuTUUID(target_id)
        if menu == None:
            return []
        menu_items = self.getMenuContent(menu.id, PULSE2_IMAGING_MENU_BOOTSERVICE, start, end, filter)
        return menu_items

    def countBootServicesOnTargetById(self, target_id, filter):
        menu = self.getTargetsMenuTUUID(target_id)
        if menu == None:
            return 0
        count_items = self.countMenuContent(menu.id, PULSE2_IMAGING_MENU_BOOTSERVICE, filter)
        return count_items

    def isLocalBootService(self, mi_uuid, session = None):
        session_need_to_close = False
        if session == None:
            session_need_to_close = True
            session = create_session()

        mi = session.query(MenuItem).add_entity(Entity)
        mi = mi.select_from(self.menu_item.join(self.menu).outerjoin(self.target).outerjoin(self.entity, or_(self.entity.c.id == self.target.c.fk_entity, self.entity.c.fk_default_menu == self.menu.c.id)))
        mi = mi.filter(and_(self.menu_item.c.id == uuid2id(mi_uuid), self.entity.c.id != None)).first()
        loc_id = mi[1].uuid

        q = session.query(BootService).add_entity(BootServiceOnImagingServer)
        q = q.select_from(self.boot_service \
                .join(self.boot_service_in_menu).join(self.menu_item) \
                .outerjoin(self.boot_service_on_imaging_server, self.boot_service.c.id == self.boot_service_on_imaging_server.c.fk_boot_service) \
                .outerjoin(self.imaging_server, self.imaging_server.c.id == self.boot_service_on_imaging_server.c.fk_imaging_server) \
                .outerjoin(self.entity))
        q = q.filter(or_(self.boot_service_on_imaging_server.c.fk_boot_service == None, self.entity.c.uuid == loc_id))
        q = q.filter(self.menu_item.c.id == uuid2id(mi_uuid))
        q = q.first()

        ret = (q[1] != None)

        if session_need_to_close:
            session.close()
        return ret

    ######################
    def getBootMenu(self, target_id, start, end, filter):
        menu = self.getTargetsMenuTUUID(target_id)
        if menu == None:
            return []
        menu_items = self.getMenuContent(menu.id, PULSE2_IMAGING_MENU_ALL, start, end, filter)
        return menu_items

    def countBootMenu(self, target_id, filter):
        menu = self.getTargetsMenuTUUID(target_id)
        if menu == None:
            return 0
        count_items = self.countMenuContent(menu.id, PULSE2_IMAGING_MENU_ALL, filter)
        return count_items

    def getEntityBootMenu(self, loc_id, start, end, filter):
        menu = self.getEntityDefaultMenu(loc_id)
        if menu == None:
            return []
        menu_items = self.getMenuContent(menu.id, PULSE2_IMAGING_MENU_ALL, start, end, filter)
        return menu_items

    def countEntityBootMenu(self, loc_id, filter):
        menu = self.getEntityDefaultMenu(loc_id)
        if menu == None:
            return 0
        count_items = self.countMenuContent(menu.id, PULSE2_IMAGING_MENU_ALL, filter)
        return count_items

    ######################
    def __moveItemInMenu(self, menu, mi_uuid, reverse = False):
        session = create_session()
        mis = self.getMenuContent(menu.id, PULSE2_IMAGING_MENU_ALL, 0, -1, '', session)
        if reverse:
            mis.sort(lambda x,y: cmp(y.order, x.order))
        move = False
        mod_mi = [None, None]
        for mi in mis:
            if move:
                move = False
                mod_mi[1] = mi
            if str(mi.id) == str(uuid2id(mi_uuid)):
                move = True
                mod_mi[0] = mi
        if mod_mi[0] != None and mod_mi[1] != None:
            ord = mod_mi[0].order
            mod_mi[0].order = mod_mi[1].order
            mod_mi[1].order = ord
            session.save_or_update(mod_mi[0])
            session.save_or_update(mod_mi[1])
            session.flush()
            session.close()
        else:
            session.close()
            return False
        return True

    def moveItemUpInMenu(self, target_uuid, mi_uuid):
        menu = self.getTargetsMenuTUUID(target_uuid)
        ret = self.__moveItemInMenu(menu, mi_uuid, True)
        return ret

    def moveItemUpInMenu4Location(self, loc_id, mi_uuid):
        menu = self.getEntityDefaultMenu(loc_id)
        ret = self.__moveItemInMenu(menu, mi_uuid, True)
        return ret

    def moveItemDownInMenu(self, target_uuid, mi_uuid):
        menu = self.getTargetsMenuTUUID(target_uuid)
        ret = self.__moveItemInMenu(menu, mi_uuid)
        return ret

    def moveItemDownInMenu4Location(self, loc_id, mi_uuid):
        menu = self.getEntityDefaultMenu(loc_id)
        ret = self.__moveItemInMenu(menu, mi_uuid)
        return ret

    ##################################
    # ImagingServer
    def countImagingServerByPackageServerUUID(self, uuid):
        session = create_session()
        q = session.query(ImagingServer).filter(self.imaging_server.c.packageserver_uuid == uuid).count()
        session.close()
        return q

    def getImagingServerByUUID(self, uuid, session = None):
        session_need_to_close = False
        if session == None:
            session_need_to_close = True
            session = create_session()
        q = session.query(ImagingServer).filter(self.imaging_server.c.id == uuid2id(uuid)).first()
        if session_need_to_close:
            session.close()
        return q

    def getImagingServerByEntityUUID(self, uuid, session = None):
        session_need_to_close = False
        if session == None:
            session_need_to_close = True
            session = create_session()
        q = session.query(ImagingServer).select_from(self.imaging_server.join(self.entity)).filter(self.entity.c.uuid == uuid).first()
        if session_need_to_close:
            session.close()
        return q

    def getImagingServerByPackageServerUUID(self, uuid, with_entity = False):
        session = create_session()
        q = session.query(ImagingServer)
        if with_entity:
            q = q.add_entity(Entity).select_from(self.imaging_server.join(self.entity))
        q = q.filter(self.imaging_server.c.packageserver_uuid == uuid).all()
        session.close()
        return q

    def registerImagingServer(self, name, url, uuid):
        session = create_session()
        ims = ImagingServer()
        ims.name = name
        ims.url = url
        ims.fk_entity = 1 # the 'NEED_ASSOCIATION' entity
        ims.packageserver_uuid = uuid
        session.save(ims)
        session.flush()
        session.close()
        return ims.id

    def __getEntityByUUID(self, session, loc_id):
        return session.query(Entity).filter(self.entity.c.uuid == loc_id).first()

    def getMenuByUUID(self, menu_uuid, session = None):
        session_need_to_close = False
        if session == None:
            session_need_to_close = True
            session = create_session()
        q = session.query(Menu).filter(self.menu.c.id == uuid2id(menu_uuid)).first()
        if session_need_to_close:
            session.close()
        return q

    def getProtocolByUUID(self, uuid, session = None):
        session_need_to_close = False
        if session == None:
            session_need_to_close = True
            session = create_session()
        q = session.query(Protocol).filter(self.protocol.c.id == uuid2id(uuid)).first()
        if session_need_to_close:
            session.close()
        return q

    def getProtocolByLabel(self, label, session = None):
        session_need_to_close = False
        if session == None:
            session_need_to_close = True
            session = create_session()
        q = session.query(Protocol).filter(self.protocol.c.label == label).first()
        if session_need_to_close:
            session.close()
        return q

    def __modifyMenu(self, menu_uuid, params, session = None):
        session_need_to_close = False
        if session == None:
            session_need_to_close = True
            session = create_session()
        menu = self.getMenuByUUID(menu_uuid, session)
        need_to_be_save = False
        if params.has_key('default_name') and menu.default_name != params['default_name']:
            need_to_be_save = True
            menu.default_name = params['default_name']
        if params.has_key('timeout') and menu.timeout != params['timeout']:
            need_to_be_save = True
            menu.timeout = params['timeout']
        if params.has_key('background_uri') and menu.background_uri != params['background_uri']:
            need_to_be_save = True
            menu.background_uri = params['background_uri']
        if params.has_key('message') and menu.message != params['message']:
            need_to_be_save = True
            menu.message = params['message']

        if params.has_key('protocol'):
            proto = self.getProtocolByUUID(params['protocol'], session)
            if proto and menu.fk_protocol != proto.id:
                need_to_be_save = True
                menu.fk_protocol = proto.id

        if need_to_be_save:
            session.save_or_update(menu)
        if session_need_to_close:
            session.flush()
            session.close()
        return menu

    def modifyMenu(self, menu_uuid, params):
        self.__modifyMenu(menu_uuid, params)
        return True

    def __getDefaultMenu(self, session):
        return session.query(Menu).filter(self.menu.c.id == 1).first()
    def __getDefaultMenuItem(self, session, menu_id = 1):
        default_item = session.query(MenuItem).filter(and_(self.menu.c.id == menu_id, self.menu.c.fk_default_item == self.menu_item.c.id)).first()
        default_item_WOL = session.query(MenuItem).filter(and_(self.menu.c.id == menu_id, self.menu.c.fk_default_item_WOL == self.menu_item.c.id)).first()
        return [default_item, default_item_WOL]
    def __getDefaultMenuMenuItems(self, session):
        return self.__getMenuItemsInMenu(session, 1)
    def __getMenuItemsInMenu(self, session, menu_id):
        return session.query(MenuItem).add_entity(BootServiceInMenu).select_from(self.menu_item.join(self.boot_service_in_menu)).filter(self.menu_item.c.fk_menu == menu_id).all()

    def __duplicateDefaultMenuItem(self, session, loc_id = None, p_id = None):
        # warning ! cant be an image !
        default_list = []
        if p_id != None:
            # get the profile menu
            menu = self.getTargetMenu(p_id, PULSE2_IMAGING_TYPE_PROFILE, session)
            default_list = self.__getMenuItemsInMenu(session, menu.id)
            mi = self.__getDefaultMenuItem(session, menu.id)
        elif loc_id != None:
            # get the entity menu
            menu = self.getEntityDefaultMenu(loc_id, session)
            default_list = self.__getMenuItemsInMenu(session, menu.id)
            mi = self.__getDefaultMenuItem(session, menu.id)
        else:
            # get the default menu
            default_list = self.__getDefaultMenuMenuItems(session)
            mi = self.__getDefaultMenuItem(session)
        ret = []
        mi_out = [0,0]
        for default_menu_item, default_bsim in default_list:
            menu_item = MenuItem()
            menu_item.order = default_menu_item.order
            menu_item.hidden = default_menu_item.hidden
            menu_item.hidden_WOL = default_menu_item.hidden_WOL
            menu_item.fk_menu = 1 # default Menu, need to be change as soon as we have the menu id!
            session.save(menu_item)
            ret.append(menu_item)
            session.flush()
            if mi[0].id == default_menu_item.id:
                mi_out[0] = menu_item.id
            if mi[1].id == default_menu_item.id:
                mi_out[1] = menu_item.id
            bsim = BootServiceInMenu()
            bsim.fk_menuitem = menu_item.id
            bsim.fk_bootservice = default_bsim.fk_bootservice
            session.save(bsim)
        session.flush()
        return [ret, mi_out]

    def __duplicateDefaultMenu(self, session):
        default_menu = self.__getDefaultMenu(session)
        return self.__duplicateMenu(session, default_menu)

    def __duplicateMenu(self, session, default_menu, loc_id = None, p_id = None):
        menu = Menu()
        menu.default_name = default_menu.default_name
        menu.fk_name = default_menu.fk_name
        menu.timeout = default_menu.timeout
        menu.background_uri = default_menu.background_uri
        menu.message = default_menu.message
        menu.fk_protocol = default_menu.fk_protocol
        menu_items, mi = self.__duplicateDefaultMenuItem(session, loc_id, p_id)
        menu.fk_default_item = mi[0]
        menu.fk_default_item_WOL = mi[1]
        menu.fk_synchrostate = 1
        session.save(menu)
        session.flush()
        for menu_item in menu_items:
            menu_item.fk_menu = menu.id
            session.save_or_update(menu_item)
        return menu

    def __createMenu(self, session, params):
        menu = Menu()
        menu.default_name = params['default_name']
        menu.timeout = params['timeout']
        menu.background_uri = params['background_uri']
        menu.message = params['message']
        if params.has_key('protocol'):
            proto = self.getProtocolByLabel(params['protocol'], session)
            if proto:
                menu.fk_protocol = proto.id
        if not menu.fk_protocol:
            proto = self.getProtocolByLabel(self.config.web_def_default_protocol, session)
            menu.fk_protocol = proto.id
        menu.fk_default_item = 0
        menu.fk_default_item_WOL = 0
        menu.fk_synchrostate = 1
        menu.fk_name = 0
        session.save(menu)
        return menu

    def __createEntity(self, session, loc_id, loc_name, menu_id):
        e = Entity()
        e.name = loc_name
        e.uuid = loc_id
        e.fk_default_menu = menu_id
        session.save(e)
        return e

    def linkImagingServerToEntity(self, is_uuid, loc_id, loc_name):
        session = create_session()
        imaging_server = self.getImagingServerByUUID(is_uuid, session)
        if imaging_server == None:
            raise "%s:No server exists with that uuid (%s)" % (ERR_IMAGING_SERVER_DONT_EXISTS, is_uuid)
        location = self.__getEntityByUUID(session, loc_id)
        if location != None:
            raise "%s:This entity already exists (%s) cant be linked again" % (ERR_ENTITY_ALREADY_EXISTS, loc_id)

        # menu = self.__createMenu(session, self.default_params)
        menu = self.__duplicateDefaultMenu(session)
        session.flush()
        location = self.__createEntity(session, loc_id, loc_name, menu.id)
        session.flush()

        imaging_server.fk_entity = location.id
        session.save_or_update(imaging_server)
        session.flush()
        session.close()
        return True

    def __AllNonLinkedImagingServer(self, session, filter):
        q = session.query(ImagingServer).filter(self.imaging_server.c.fk_entity == 1)
        if filter and filter != '':
            q = q.filter(or_(self.imaging_server.c.name.like('%'+filter+'%'), self.imaging_server.c.url.like('%'+filter+'%'), self.imaging_server.c.uuid.like('%'+filter+'%')))
        return q

    def getAllNonLinkedImagingServer(self, start, end, filter):
        session = create_session()
        q = self.__AllNonLinkedImagingServer(session, filter)
        if end != -1:
            q = q.offset(int(start)).limit(int(end)-int(start))
        else:
            q = q.all()
        session.close()
        return q

    def countAllNonLinkedImagingServer(self, filter):
        session = create_session()
        q = self.__AllNonLinkedImagingServer(session, filter)
        q = q.count()
        session.close()
        return q

    def doesLocationHasImagingServer(self, loc_id):
        session = create_session()
        q = session.query(ImagingServer).select_from(self.imaging_server.join(self.entity)).filter(self.entity.c.uuid == loc_id).count()
        return (q == 1)

    def setImagingServerConfig(self, location, config):
        session = create_session()
        imaging_server = self.getImagingServerByEntityUUID(location, session)
        # modify imaging_server
        # session.save(imaging_server)
        # session.flush()
        session.close()
        return True

    # Protocols
    def getAllProtocols(self):
        session = create_session()
        q = session.query(Protocol).all()
        session.close()
        return q

    ######### REGISTRATION
    def isTargetRegister(self, uuid, target_type, session = None):
        session_need_to_close = False
        if session == None:
            session_need_to_close = True
            session = create_session()

        if type(uuid) == list:
            q = session.query(Target).filter(and_(self.target.c.uuid.in_(uuid), self.target_type.c.id == target_type)).all()
        else:
            q = session.query(Target).filter(and_(self.target.c.uuid == uuid, self.target_type.c.id == target_type)).first()
        ret = (q != None)

        if session_need_to_close:
            session.close()
        return ret

    def __createTarget(self, session, uuid, name, type, entity_id, menu_id, params):
        target = Target()
        target.uuid = uuid
        target.name = name
        target.type = type
        target.kernel_parameters = ''
        target.image_parameters = ''
        target.fk_entity = entity_id
        target.fk_menu = menu_id
        session.save(target)
        return target

    ######### SYNCHRO
    def getTargetsThatNeedSynchroInEntity(self, loc_id, target_type, session = None):
        session_need_to_close = False
        if session == None:
            session_need_to_close = True
            session = create_session()

        q = session.query(Target).add_entity(SynchroState)
        q = q.select_from(self.target.join(self.menu).join(self.entity, self.target.c.fk_entity == self.entity.c.id))
        q = q.filter(and_(
                self.entity.c.uuid == loc_id, \
                self.menu.c.fk_synchrostate.in_(PULSE2_IMAGING_SYNCHROSTATE_TODO, PULSE2_IMAGING_SYNCHROSTATE_INIT_ERROR), \
                self.target.c.type == target_type \
            )).all()

        if session_need_to_close:
            session.close()
        return q

    def getComputersThatNeedSynchroInEntity(self, loc_id, session = None):
        return self.getTargetsThatNeedSynchroInEntity(loc_id, PULSE2_IMAGING_TYPE_COMPUTER, session)
    def getProfilesThatNeedSynchroInEntity(self, loc_id, session = None):
        return self.getTargetsThatNeedSynchroInEntity(loc_id, PULSE2_IMAGING_TYPE_PROFILE, session)
        
    def __getSynchroStates(self, uuids, target_type, session):
        q = session.query(SynchroState).add_entity(Menu)
        q = q.select_from(self.synchro_state.join(self.menu).join(self.target, self.menu.c.id == self.target.c.fk_menu))
        q = q.filter(and_(self.target.c.uuid.in_(uuids), self.target.c.type == target_type)).all()
        return q

    def getTargetsSynchroState(self, uuids, target_type):
        session = create_session()
        q = self.__getSynchroStates(uuids, target_type, session)
        session.close()
        if q:
            return map(lambda x: x[0], q)
        return False

    def getLocationSynchroState(self, uuid):
        session = create_session()

        q2 = session.query(SynchroState)
        q2 = q2.select_from(self.synchro_state.join(self.menu).join(self.entity, self.entity.c.fk_default_menu == self.menu.c.id))
        q2 = q2.filter(self.entity.c.uuid == uuid).first()

        if q2.id == 3 or q2.id == 4: # running
            session.close()
            return q2
        # in the 2 other cases we have to check the state of the content of this entity

        q1 = session.query(SynchroState)
        q1 = q1.select_from(self.synchro_state.join(self.menu).join(self.target, self.menu.c.id == self.target.c.fk_menu).join(self.entity, self.entity.c.id == self.target.c.fk_entity))
        q1 = q1.filter(self.entity.c.uuid == uuid).all()

        session.close()

        a_state = [0, 0]
        for q in q1:
            print q.toH()
            if q.id == 3 or q.id == 4: # running
                return q
            a_state[q.id - 1] += 1
        if a_state[0] == 0:
            return {'id':2, 'label':'DONE'}
        return {'id':1, 'label':'TODO'}

    def setLocationSynchroState(self, uuid, state):
        session = create_session()
        q2 = session.query(SynchroState).add_entity(Menu)
        q2 = q2.select_from(self.synchro_state.join(self.menu).join(self.entity, self.entity.c.fk_default_menu == self.menu.c.id))
        q2 = q2.filter(self.entity.c.uuid == uuid).first()

        if q2 :
            synchro_state, menu = q2
            menu.fk_synchrostate = state
            session.save_or_update(menu)
        else :
            logging.getLogger().warn("Imaging.setLocationSynchroState : failed to set synchro_state")

        session.flush()
        session.close()
        return True

    def changeTargetsSynchroState(self, uuids, target_type, state):
        session = create_session()
        synchro_states = self.__getSynchroStates(uuids, target_type, session)
        for synchro_state, menu in synchro_states:
            menu.fk_synchrostate = state
            session.save_or_update(menu)
        session.flush()
        session.close()
        return True

    ######### MENUS
    def setMyMenuTarget(self, uuid, params, type):
        session = create_session()
        menu = self.getTargetMenu(uuid, type, session)
        location_id = None
        p_id = None
        if not menu:
            if type == PULSE2_IMAGING_TYPE_COMPUTER:
                profile = ComputerProfileManager().getComputersProfile(uuid)
                default_menu = None
                if profile:
                    default_menu = self.getTargetMenu(profile.id, PULSE2_IMAGING_TYPE_PROFILE, session)
                if default_menu == None or not profile:
                    location = ComputerLocationManager().getMachinesLocations([uuid])
                    loc_id = location[uuid]['uuid']
                    location_id = loc_id
                    default_menu = self.getEntityDefaultMenu(loc_id, session)
                else:
                    p_id = profile.id
            elif type == PULSE2_IMAGING_TYPE_PROFILE:
                m_uuids = map(lambda c: c.uuid, ComputerProfileManager().getProfileContent(uuid))
                locations = ComputerLocationManager().getMachinesLocations(m_uuids)
                # WARNING! here we take the location that is the most represented, it's wrong!
                # we have to decide how do we do with cross location profiles
                # TODO!
                loc_id = locations[m_uuids[0]]['uuid']
                location_id = loc_id
                default_menu = self.getEntityDefaultMenu(location_id, session)
            else:
                raise "%s:Don't know that type of target : %s"%(ERR_DEFAULT, type)
            menu = self.__duplicateMenu(session, default_menu, loc_id, p_id)
            menu = self.__modifyMenu(id2uuid(menu.id), params, session)
            session.flush()
        else:
            menu = self.__modifyMenu(id2uuid(menu.id), params, session)

        if not self.isTargetRegister(uuid, type, session):
            if location_id == None:
                location = ComputerLocationManager().getMachinesLocations([uuid])
                location_id = location[uuid]['uuid']
            loc = session.query(Entity).filter(self.entity.c.uuid == location_id).first()
            target = self.__createTarget(session, uuid, params['target_name'], type, loc.id, menu.id, params)
            # TODO : what do we do with target ?

        session.flush()
        session.close()
        return [True]

    def getMyMenuTarget(self, uuid, type):
        session = create_session()
        muuid = False
        if type == PULSE2_IMAGING_TYPE_COMPUTER:
            # if registered, get the computer menu and finish
            if self.isTargetRegister(uuid, type, session):
                whose = [uuid, type]
                menu = self.getTargetMenu(uuid, type, session)
                session.close()
                return [whose, menu]
            # else get the profile id
            else:
                profile = ComputerProfileManager().getComputersProfile(uuid)
                muuid = uuid
                if profile:
                    uuid = profile.id # WARNING we must pass in UUIDs!

        # if profile is registered, get the profile menu and finish
        if uuid and self.isTargetRegister(uuid, PULSE2_IMAGING_TYPE_PROFILE, session):
            whose = [uuid, PULSE2_IMAGING_TYPE_PROFILE]
            menu = self.getTargetMenu(uuid, PULSE2_IMAGING_TYPE_PROFILE, session)
        # else get the entity menu
        else:
            whose = False
            if muuid:
                location = ComputerLocationManager().getMachinesLocations([muuid])
                loc_id = location[muuid]['uuid']
            else:
                m_uuids = map(lambda c: c.uuid, ComputerProfileManager().getProfileContent(uuid))
                locations = ComputerLocationManager().getMachinesLocations(m_uuids)
                # WARNING! here we take the location that is the most represented, it's wrong!
                # we have to decide how do we do with cross location profiles
                # TODO!
                loc_id = locations[m_uuids[0]]['uuid']
            menu = self.getEntityDefaultMenu(loc_id, session)
        if menu == None:
            menu = False

        session.close()
        return [whose, menu]

    ######### POST INSTALL SCRIPT
    def isLocalPostInstallScripts(self, pis_uuid, session = None):
        session_need_to_close = False
        if session == None:
            session_need_to_close = True
            session = create_session()

        q = session.query(PostInstallScript).add_entity(PostInstallScriptOnImagingServer)
        q = q.select_from(self.post_install_script \
                .outerjoin(self.post_install_script_on_imaging_server, self.post_install_script_on_imaging_server.c.fk_post_install_script == self.post_install_script.c.id) \
                .outerjoin(self.imaging_server, self.post_install_script_on_imaging_server.c.fk_imaging_server == self.imaging_server.c.id) \
                .outerjoin(self.entity))
        q = q.filter(or_(self.post_install_script_on_imaging_server.c.fk_post_install_script == None, self.entity.c.uuid == pis_uuid))
        q = q.filter(self.post_install_script.c.id == uuid2id(pis_uuid))
        q = q.first()

        ret = (q[1] != None)

        if session_need_to_close:
            session.close()
        return ret

    def __AllPostInstallScripts(self, session, location, filter, is_count = False):
        # PostInstallScripts are not specific to an Entity
        q = session.query(PostInstallScript)
        if not is_count:
            q = q.add_entity(PostInstallScriptOnImagingServer)
            q = q.select_from(self.post_install_script \
                    .outerjoin(self.post_install_script_on_imaging_server, self.post_install_script_on_imaging_server.c.fk_post_install_script == self.post_install_script.c.id) \
                    .outerjoin(self.imaging_server, self.post_install_script_on_imaging_server.c.fk_imaging_server == self.imaging_server.c.id) \
                    .outerjoin(self.entity))
            q = q.filter(or_(self.post_install_script_on_imaging_server.c.fk_post_install_script == None, self.entity.c.uuid == location))
        q = q.filter(or_(self.post_install_script.c.default_name.like('%'+filter+'%'), self.post_install_script.c.default_desc.like('%'+filter+'%')))
        return q

    def __mergePostInstallScriptOnImagingServerInPostInstallScript(self, postinstallscript_list):
        ret = []
        for postinstallscript, postinstallscript_on_imagingserver in postinstallscript_list:
            setattr(postinstallscript, 'is_local', (postinstallscript_on_imagingserver != None))
            ret.append(postinstallscript)
        return ret

    def getAllTargetPostInstallScript(self, target_uuid, start, end, filter):
        session = create_session()
        loc = session.query(Entity).select_from(self.entity.join(self.target)).filter(self.target.c.uuid == target_uuid).first()
        session.close()
        location = id2uuid(loc.id)
        return self.getAllPostInstallScripts(location, start, end, filter)

    def countAllTargetPostInstallScript(self, target_uuid, filter):
        session = create_session()
        loc = session.query(Entity).select_from(self.entity.join(self.target)).filter(self.target.c.uuid == target_uuid).first()
        session.close()
        location = id2uuid(loc.id)
        return self.countAllPostInstallScripts(location, filter)

    def getAllPostInstallScripts(self, location, start, end, filter):
        session = create_session()
        q = self.__AllPostInstallScripts(session, location, filter)
        if end != -1:
            q = q.offset(int(start)).limit(int(end)-int(start))
        else:
            q = q.all()
        session.close()
        q = self.__mergePostInstallScriptOnImagingServerInPostInstallScript(q)
        return q

    def countAllPostInstallScripts(self, location, filter):
        session = create_session()
        q = self.__AllPostInstallScripts(session, location, filter, True)
        q = q.count()
        session.close()
        return q

    def getPostInstallScript(self, pis_uuid, session = None):
        session_need_to_close = False
        if session == None:
            session_need_to_close = True
            session = create_session()

        q = session.query(PostInstallScript).add_entity(PostInstallScriptOnImagingServer)
        q = q.select_from(self.post_install_script.outerjoin(self.post_install_script_on_imaging_server))
        q = q.filter(self.post_install_script.c.id == uuid2id(pis_uuid)).first()
        q = self.__mergePostInstallScriptOnImagingServerInPostInstallScript([q])

        if session_need_to_close:
            session.close()
        return q[0]

    def delPostInstallScript(self, pis_uuid):
        session = create_session()
        pis = self.getPostInstallScript(pis_uuid, session)
        if not pis.is_local:
            return False
        session.delete(pis)
        session.flush()
        session.close
        return True

    def getImagesPostInstallScript(self, ims, session = None):
        session_need_to_close = False
        if session == None:
            session_need_to_close = True
            session = create_session()

        q = session.query(PostInstallScript).add_entity(Image)
        q = q.select_from(self.post_install_script.join(self.post_install_script_in_image).join(self.image))
        q = q.filter(self.image.c.id.in_(ims)).all()

        if session_need_to_close:
            session.close()
        return q

    def editPostInstallScript(self, pis_uuid, params):
        session = create_session()
        pis = self.getPostInstallScript(pis_uuid, session)
        need_to_be_save = False
        if pis.default_name != params['default_name']:
            need_to_be_save = True
            pis.default_name = params['default_name']
        if pis.default_desc != params['default_desc']:
            need_to_be_save = True
            pis.default_desc = params['default_desc']
        if pis.value != params['value']:
            need_to_be_save = True
            pis.value = params['value']

        if need_to_be_save:
            session.save_or_update(pis)
            session.flush()
        session.close()
        return True

    def addPostInstallScript(self, loc_id, params):
        session = create_session()
        pis = PostInstallScript()
        pis.default_name = params['default_name']
        pis.default_desc = params['default_desc']
        pis.value = params['value']
        session.save(pis)
        session.flush()
        # link it to the location because it's a local script
        imaging_server = self.getImagingServerByEntityUUID(loc_id, session)
        pisois = PostInstallScriptOnImagingServer()
        pisois.fk_post_install_script = pis.id
        pisois.fk_imaging_server = imaging_server.id
        session.save(pisois)
        session.flush()
        session.close()
        return True

def id2uuid(id):
    return "UUID%d" % id
def uuid2id(uuid):
    return uuid.replace("UUID", "")

###########################################################
class DBObject(object):
    to_be_exported = ['id', 'name', 'label']
    need_iteration = []
    def getUUID(self):
        return id2uuid(self.id)
    def to_h(self):
        return self.toH()
    def toH(self, level = 0):
        ImagingDatabase().completeNomenclatureLabel(self)
        ret = {}
        for i in dir(self):
            if i in self.to_be_exported:
                ret[i] = getattr(self, i)
            if i in self.need_iteration and level < 1:
                # we dont want to enter in an infinite loop
                # and generaly we dont need more levels
                ret[i] = getattr(self, i).toH(level+1)
        ret['imaging_uuid'] = self.getUUID()
        return ret

class BootService(DBObject):
    to_be_exported = ['id', 'value', 'default_desc', 'uri', 'is_local', 'default_name']
    need_iteration = ['menu_item']

class BootServiceInMenu(DBObject):
    pass

class BootServiceOnImagingServer(DBObject):
    pass

class Entity(DBObject):
    to_be_exported = ['id', 'name', 'uuid']

class Image(DBObject):
    to_be_exported = ['id', 'path', 'checksum', 'size', 'desc', 'is_master', 'creation_date', 'fk_creator', 'name', 'is_local', 'uuid', 'mastered_on_target_uuid']
    need_iteration = ['menu_item']

class ImageInMenu(DBObject):
    pass

class ImageOnImagingServer(DBObject):
    pass

class ImagingServer(DBObject):
    to_be_exported = ['id', 'name', 'url', 'packageserver_uuid', 'recursive', 'fk_entity']

class Internationalization(DBObject):
    to_be_exported = ['id', 'label', 'fk_language']

class Language(DBObject):
    to_be_exported = ['id', 'label']

class MasteredOn(DBObject):
    to_be_exported = ['id', 'timestamp', 'title', 'completeness', 'detail', 'fk_mastered_on_state', 'fk_image', 'fk_target', 'mastered_on_state', 'image']
    need_iteration = ['target']

class MasteredOnState(DBObject):
    to_be_exported = ['id', 'label']

class Menu(DBObject):
    to_be_exported = ['id', 'default_name', 'fk_name', 'timeout', 'background_uri', 'message', 'fk_default_item', 'fk_default_item_WOL', 'fk_protocol', 'protocol', 'synchrostate']

class MenuItem(DBObject):
    to_be_exported = ['id', 'default_name', 'order', 'hidden', 'hidden_WOL', 'fk_menu', 'fk_name', 'default', 'default_WOL', 'desc']
    need_iteration = ['boot_service', 'image']

class Partition(DBObject):
    to_be_exported = ['id', 'filesystem', 'size', 'fk_image']

class PostInstallScript(DBObject):
    to_be_exported = ['id', 'default_name', 'value', 'default_desc', 'is_local']

class PostInstallScriptInImage(DBObject):
    pass

class PostInstallScriptOnImagingServer(DBObject):
    pass

class Protocol(DBObject):
    to_be_exported = ['id', 'label']

class SynchroState(DBObject):
    to_be_exported = ['id', 'label']

class Target(DBObject):
    to_be_exported = ['id', 'name', 'uuid', 'type', 'fk_entity', 'fk_menu']

class TargetType(DBObject):
    to_be_exported = ['id', 'label']

class User(DBObject):
    to_be_exported = ['id', 'login']

# -*- coding: utf-8; -*-
#
# (c) 2004-2007 Linbox / Free&ALter Soft, http://linbox.com
# (c) 2007-2009 Mandriva, http://www.mandriva.com
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
Contains classes that define records for the audit system
"""

from sqlalchemy import *
from classes import *

class AuditRecord:

    """
    Base class for a audit record object
    """
    
    def __init__(self, module, event, user, object, param, initiator, source, previous, current):
        """
        Create a AuditRecord instance which contains all information that will
        be logged into database.
        
        @param module: module name
        @type module: string
        @param event: event name 
        @type event: string
        @param user: user name
        @type user: string
        @param object: list tuple of object which contains object uri and object type [('object','typeobject')...]
        @type object: list
        @param client: tuple which represent client (clienthost, clienttype)
        @type client: tuple
        @param param: parameters
        @type param: dict 
        @param agent: represent agent hostname
        @type agent: string
        """
        # module string
        self.module = module
        assert(type(self.module) == unicode)
        # action string
        self.event = event
        assert(type(self.event) == unicode)
        # String
        self.user=user
        assert(type(self.user) == unicode)
        # Dictionnary of string
        self.parameters = param
        assert(type(self.parameters) == dict)
        # list of couple (object, type)
        self.objects=object
        assert(type(self.objects) == tuple)
        # 
        self.initiator = initiator
        assert(type(self.initiator) == tuple)
        assert(len(self.initiator) == 2)
        # 
        self.source = source
        assert(type(source) == str)
        # list of string list
        self.previousattribute=previous
        # list of string list
        self.currentattribute=current


class AuditRecordDB(AuditRecord):

    """
    Class for objects that store an audit record into a database
    """

    def __init__(self, parent, session, module, event, user, objects, param, initiator, source, current, previous):
        """ 
        Insert New log in database 
        @param action: action name 
        @type action: string
        @param module: module name
        @type action: string
        @param module: module name
        @type module: string
        @param user: user name
        @type user: string
        @param objects: list tuple of object which contains object uri and object type [('object','typeobject')...]
        @type objects: list
        @param client: tuple which represent client (clienthost, clienttype)
        @type client: tuple
        @param param: parameters
        @type param: dict 
        @param agent: represent agent hostname
        @type agent: string
        """
        AuditRecord.__init__(self, module, event, user, objects, param, initiator, source, current, previous)
        self.session = session
        self.session.begin()
        
        # get module object from database
        bdmodule = self.session.query(Module).filter(parent.module_table.c.name==module).first()
        # insert module object in database if it is not available
        if bdmodule == None:
            bdmodule = Module()
            bdmodule.name = module
            self.session.save(bdmodule)
            self.session.flush()

        # get event object from database
        bdevent = self.session.query(Event).filter(and_(parent.event_table.c.name == event, parent.event_table.c.module_id == bdmodule.id)).first()
        # insert event object in database if it is not available
        if bdevent == None:
            bdevent = Event()
            bdevent.module_id = bdmodule.id
            bdevent.name = event
            self.session.save(bdevent)
            self.session.flush()

        # get initiator object
        bdinitiator = self.session.query(Initiator).filter(and_(parent.initiator_table.c.application == initiator[1], parent.initiator_table.c.hostname == initiator[0])).first()
        # put it in database if it is not available
        if bdinitiator == None:
            bdinitiator = Initiator()
            bdinitiator.application = initiator[1]
            bdinitiator.hostname = initiator[0]
            self.session.save(bdinitiator)
            self.session.flush()

        # get source object
        bdsource = self.session.query(Source).filter(parent.source_table.c.hostname == source).first()
        # put it in database if not available
        if bdsource == None:
            bdsource = Source()
            bdsource.hostname = source
            self.session.save(bdsource)
            self.session.flush()

        # get user type
        utype = self.session.query(Type).filter(parent.type_table.c.type == 'USER').first()
        if utype == None:
            utype = Type()
            utype.type = 'USER'
            self.session.save(utype)
            self.session.flush()

        # get user object
        bduser = self.session.query(Object).filter(and_(parent.object_table.c.uri == user, parent.object_table.c.type_id == utype.id)).first()
        if bduser == None:
            bduser = Object()
            bduser.uri = user
            bduser.type_id = utype.id
            self.session.save(bduser)
            self.session.flush()

        # Fill in record to emit
        self.record = Record()
        self.record.event_id = bdevent.id
        self.record.module_id = bdmodule.id
        self.record.source_id = bdsource.id
        self.record.initiator_id = bdinitiator.id
        self.record.user_id = bduser.id
        # Set result status to undone
        self.record.result = False
        # Insert Object_Log
        self.session.save(self.record)
        self.session.flush()
        
        parentobj=None
        if objects != None:
            for i,j in objects:
                #Get or Insert Type id of object
                bdtype = self.session.query(Type).filter(parent.type_table.c.type==j).first()
                if bdtype == None:
                    bdtype = Type()
                    bdtype.type = j
                    self.session.save(bdtype)
                    self.session.flush()
                
                # Object is not parent
                # l'objet peut ne pas avoir de parent
                obj = self.session.query(Object).filter(and_(parent.object_table.c.uri==i, parent.object_table.c.type_id==bdtype.id)).first()

                if obj == None:          
                    obj = Object()
                    obj.uri = i
                    obj.type_id = bdtype.id
                    
                    
                    if bdtype.id == 2:
                        obj.parent = None
                    else:
                        obj.parent = parentobj
                    self.session.save(obj)
                    self.session.flush()
                #
                # Insert in object_log table
                #
                
                parentobj = obj.id
                bdobjectlog = Object_Log()
                bdobjectlog.object_id = obj.id
                bdobjectlog.log_id = self.record.id
                self.session.save(bdobjectlog)
                self.session.flush()
                # object type is attribute
                if obj.type_id==2:
                    bdobjectlogattr=bdobjectlog
              
        #insert current value
        if current != None:
            if type(current) == tuple or type(current) == list :
                for i in current:            
                     cv = Current_Value(bdobjectlogattr, i)
                     self.session.save(cv)
            else:
                cv = Current_Value(bdobjectlogattr, current)
                self.session.save(cv)

        #insert previous value        
        if previous != None:
            if type(previous) == tuple or type(previous) == list:
                for i in previous:             
                     pv = Previous_Value(bdobjectlogattr, i)
                     self.session.save(pv)      
            else:          
                pv = Previous_Value(bdobjectlogattr, previous)
                self.session.save(pv)  

        # relations on log_parameters        
        if param != None:
            for i in param:
                if type(i)==list:
                    for j in i:
                        p = Parameters(j, str(i[j]))
                        self.record.param_log.append(p)
                else:
                    p = Parameters(i, str(param[i]))
                    self.record.param_log.append(p)
        
        self.session.save_or_update(self.record)
        self.session.flush()
        self.session.commit()
        
    def commit(self):
        """
        Valid the log and set the result attribute to True if event succeeds
        """
        self.record.result = True
        self.session.save_or_update(self.record)
        self.session.flush()
        self.session.close()
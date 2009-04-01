<?php
/**
 * (c) 2004-2007 Linbox / Free&ALter Soft, http://linbox.com
 * (c) 2007 Mandriva, http://www.mandriva.com
 *
 * $Id$
 *
 * This file is part of Mandriva Management Console (MMC).
 *
 * MMC is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * MMC is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with MMC; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

require_once("modules/dyngroup/includes/includes.php");

$MMCApp =& MMCApp::getInstance();

/* Get the base module instance */
$base = &$MMCApp->getModule('base');

/* Get the computers sub-module instance */
$submod = & $base->getSubmod('computers');

if (!empty($submod)) {

    /* Dynamic groups */

    if (isDynamicEnable()) {
        $page = new Page("computersgroupcreator",_T("Computers Group Creator","dyngroup"));
        $page->setFile("modules/dyngroup/dyngroup/tab.php");

        $tab = new Tab("tabdyn", _T("Dynamic group creation's tab", "dyngroup"));
        $page->addTab($tab);

        $tab = new Tab("tabsta", _T("Static group creation's tab", "dyngroup"));
        $page->addTab($tab);

        $tab = new Tab("tabfromfile", _T("Static group creation from import's tab", "dyngroup"));
        $page->addTab($tab);
        $submod->addPage($page);

        $page = new Page("computersgroupcreatesubedit",_T("Computers Group Creator Sub Request Editor","dyngroup"));
        $page->setFile("modules/dyngroup/dyngroup/tab.php");
        $page->setOptions(array("visible"=>False, "noACL"=>True));

        $tab = new Tab("tabdyn", _T("Dynamic group creation's tab", "dyngroup"));
        $tab->setOptions(array("noACL"=>True));
        $page->addTab($tab);

        $tab = new Tab("tabsta", _T("Static group creation's tab", "dyngroup"));
        $tab->setOptions(array("noACL"=>True));
        $page->addTab($tab);

        $tab = new Tab("tabfromfile", _T("Static group creation from import's tab", "dyngroup"));
        $tab->setOptions(array("noACL"=>True));
        $page->addTab($tab);
        $submod->addPage($page);
    
        $page = new Page("computersgroupcreatesubdel",_T("Computers Group Creator Sub Request Delete","dyngroup"));
        $page->setFile("modules/dyngroup/dyngroup/tab.php");
        $page->setOptions(array("visible"=>False, "noACL"=>True));

        $tab = new Tab("tabdyn", _T("Dynamic group creation's tab", "dyngroup"));
        $tab->setOptions(array("noACL"=>True));
        $page->addTab($tab);

        $tab = new Tab("tabsta", _T("Static group creation's tab", "dyngroup"));
        $tab->setOptions(array("noACL"=>True));
        $page->addTab($tab);

        $tab = new Tab("tabfromfile", _T("Static group creation from import's tab", "dyngroup"));
        $tab->setOptions(array("noACL"=>True));
        $page->addTab($tab);
        $submod->addPage($page);

        $page = new Page("computersgroupedit",_T("Computers Group Editor","dyngroup"));
        $page->setFile("modules/dyngroup/dyngroup/edithead.php");
        $page->setOptions(array("visible"=>False));
        $submod->addPage($page);

        $page = new Page("computersgroupsubedit",_T("Computers Group Sub Request Editor","dyngroup"));
        $page->setFile("modules/dyngroup/dyngroup/edithead.php");
        $page->setOptions(array("visible"=>False, "noACL"=>True));
        $submod->addPage($page);
    
        $page = new Page("computersgroupsubdel",_T("Computers Group Sub Request Delete","dyngroup"));
        $page->setFile("modules/dyngroup/dyngroup/edithead.php");
        $page->setOptions(array("visible"=>False, "noACL"=>True));
        $submod->addPage($page);
    
        $page = new Page("tmpdisplay",_T("Temporary result display","dyngroup"));
        $page->setFile("modules/dyngroup/dyngroup/tmpdisplay.php");
        $page->setOptions(array("visible"=>False));
        $submod->addPage($page);
    } else {
        $page = new Page("computersgroupcreator",_T("Computers Group Creator","dyngroup"));
        $page->setFile("modules/dyngroup/dyngroup/groupshead.php");
        $submod->addPage($page);

        $page = new Page("computersgroupedit",_T("Computers Group Editor","dyngroup"));
        $page->setFile("modules/dyngroup/dyngroup/groupshead.php");
        $page->setOptions(array("visible"=>False));
        $submod->addPage($page);
    }

    $page = new Page("display",_T("Display a groups of computers","dyngroup"));
    $page->setFile("modules/dyngroup/dyngroup/display.php");
    $page->setOptions(array("visible"=>False));
    $submod->addPage($page);

    $page = new Page("edit_share",_T("Share a group of computers","dyngroup"));
    $page->setFile("modules/dyngroup/dyngroup/edit_share.php");
    $page->setOptions(array("visible"=>False));
    $submod->addPage($page);

    $page = new Page("save",_T("Save a group of computers","dyngroup"));
    $page->setFile("modules/dyngroup/dyngroup/save.php");
    $page->setOptions(array("visible"=>False));
    $submod->addPage($page);

    $page = new Page("save_detail",_T("Detailed page of save a group of computers","dyngroup"));
    $page->setFile("modules/dyngroup/dyngroup/save_detail.php");
    $page->setOptions(array("visible"=>False));
    $submod->addPage($page);

    $page = new Page("list",_T("List all groups of computers","dyngroup"));
    $page->setFile("modules/dyngroup/dyngroup/list.php");
    $submod->addPage($page);

    $page = new Page("delete_group",_T("Delete a group of computers","dyngroup"));
    $page->setFile("modules/dyngroup/dyngroup/delete_group.php");
    $page->setOptions(array("visible"=>False, "noHeader" =>True));
    $submod->addPage($page);

    $page = new Page("details",_T("Group of computers details","dyngroup"));
    $page->setFile("modules/dyngroup/dyngroup/details.php");
    $page->setOptions(array("visible"=>False, "AJAX" =>True));
    $submod->addPage($page);

    $page = new Page("remove_machine",_T("Remove a computer from a computers group","dyngroup"));
    $page->setFile("modules/dyngroup/dyngroup/remove_machine.php");
    $page->setOptions(array("visible"=>False, "noHeader" =>True));
    $submod->addPage($page);

    $page = new Page("ajaxAutocompleteSearch");
    $page->setFile("modules/dyngroup/dyngroup/ajaxAutocompleteSearch.php");
    $page->setOptions(array("visible"=>False, "AJAX" =>True));
    $submod->addPage($page);

    $page = new Page("ajaxAutocompleteSearchWhere");
    $page->setFile("modules/dyngroup/dyngroup/ajaxAutocompleteSearchWhere.php");
    $page->setOptions(array("visible"=>False, "AJAX" =>True));
    $submod->addPage($page);

    $page = new Page("csv",_T("Csv's export", "dyngroup"));
    $page->setFile("modules/dyngroup/dyngroup/csv.php");
    $page->setOptions(array("visible"=>False, "noHeader"=>True));
    $submod->addPage($page);

}

unset($submod);
/* groupes dynamiques end */
?>
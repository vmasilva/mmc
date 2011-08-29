<?php
/**
 * (c) 2004-2007 Linbox / Free&ALter Soft, http://linbox.com
 * (c) 2007-2008 Mandriva, http://www.mandriva.com/
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
require("modules/samba/includes/machines.inc.php");

$filter = $_GET['filter'];
$computers = search_machines($filter);
//print_r($computers);
$names = array();
$desc = array();
$active = array();
foreach($computers as $computer) {
    $names[] = $computer[0];
    $desc[] = $computer[1];
    $active[] = $computer[2];
}

$l = new ListInfos($names, _T("Computer name", "samba"));
$l->disableFirstColumnActionLink();
$l->setCssClass("machineName");
$l->setNavBar(new AjaxNavBar(count($computers), $filter));
$l->addExtraInfo($desc, _T("Description", "samba"));
$l->addExtraInfo($active, _T("Active", "samba"));
$l->addActionItem(new ActionItem(_T("Edit"),"edit","edit","machine"));
$l->addActionItem(new ActionPopupItem(_T("Delete"),"delete","delete","machine"));
$l->setName(_("Computers"));
$l->display();

?>

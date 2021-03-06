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

require_once("modules/base/includes/computers.inc.php");

if (isset($_POST["bconfirm"])) {
    $uuid = $_POST["objectUUID"];
    $backup = ($_POST["backup"]?True:False);
    delComputer($uuid, $backup);
    if (!isXMLRPCError()) new NotifyWidgetSuccess(_("The computer has been deleted."));
    header("Location: " . urlStrRedirect("base/computers/index"));
} else {
    $uuid = urldecode($_GET["objectUUID"]);
    $f = new PopupForm(_("Delete this computer"));
    $f->push(new Table());

    $f->add(new TrFormElement(_("Do you want a backup to be done ?"), new CheckBoxTpl("backup")), array("value" => ''));
    $hidden = new HiddenTpl("objectUUID");
    $f->add($hidden, array("value" => $uuid, "hide" => True));
    $f->pop();
    $f->addValidateButton("bconfirm");
    $f->addCancelButton("bback");
    $f->display();
}


?>

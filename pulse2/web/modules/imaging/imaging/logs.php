<?

/*
 * (c) 2004-2007 Linbox / Free&ALter Soft, http://linbox.com
 * (c) 2007-2009 Mandriva, http://www.mandriva.com
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

require_once('modules/imaging/includes/includes.php');

if(isset($_GET['mod']))
    $mod = $_GET['mod'];
else 
    $mod = "none";

switch($mod) {
    case 'details':
        log_details();
        break;
    default:
        log_list();
        break;
}

function log_details() {
    echo 'details';
}

function log_list() {
    $ajax = new AjaxFilter("modules/imaging/imaging/ajaxLogs.php", "container", getParams());
    //$ajax->setRefresh(10000);
    $ajax->display();
    echo '<br/><br/><br/>';
    $ajax->displayDivToUpdate();
}

?>
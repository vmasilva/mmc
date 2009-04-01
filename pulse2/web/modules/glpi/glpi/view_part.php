<?
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

require_once("modules/glpi/includes/xmlrpc.php");

$uuid = '';
if (isset($_GET['uuid'])) {
    $uuid = $_GET['uuid'];
} elseif (isset($_GET['objectUUID'])) {
    $uuid = $_GET['objectUUID'];
}
$inv = getLastMachineGlpiPart($uuid, $_GET['part']);
if (!is_array($inv)) $inv = array();

$all = array();
$i = 0;
foreach ($inv as $line) {
    foreach ($line as $vals) {
        $all[$vals[0]][$i] = $vals[1];
    }
    $i+=1;
}

$n = null;
foreach ($all as $k => $v) {
    if ($n == null) {
        $n = new ListInfos($v, $k);
    } else {
        $n->addExtraInfo($v, $k);
    }
}
if ($n) {
    $n->drawTable(0);
}

?>

</table>

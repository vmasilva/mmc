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
require_once('modules/imaging/includes/xmlrpc.inc.php');

$params = getParams();
if (isset($_GET['gid']) && $_GET['gid'] != '') {
    $type = 'group';
    $target_uuid = isset($_GET['gid']) ? $_GET['gid'] : "";
    $target_name = isset($_GET['groupname']) ? $_GET['groupname'] : "";
} else {
    $type = '';
    $target_uuid = isset($_GET['uuid']) ? $_GET['uuid'] : "";
    if (isset($_GET['hostname'])) {
        $target_name = $_GET['hostname'];
    } elseif (isset($_GET['target_name'])) {
        $target_name = $_GET['target_name'];
    } else {
        $target_name = '';
    }
}
if (isset($params['hostname']) && !isset($target_name)) {
    $target_name = $params['hostname'];
}

function item_up() {
    $params = getParams();
    $item_uuid = $_GET['itemid'];
    $label = $_GET['itemlabel'];

    if (isset($_GET['gid'])) {
        $type = 'group';
        $gid = $params['gid'];
        $ret = xmlrpc_moveItemUpInMenu($gid, $type, $item_uuid);
    } else {
        $type = '';
        $uuid = $params['uuid'];
        $ret = xmlrpc_moveItemUpInMenu($uuid, $type, $item_uuid);
    }
    if ($ret) {
    /* insert notification code here if needed */
    } else {
        $str = sprintf(_T("Failed to move item <strong>%s</strong> in the boot menu", "imaging"), urldecode($label));
        new NotifyWidgetFailure($str);
    }

    header("Location: " . urlStrRedirect("base/computers/".$type."imgtabs", $params));
}

function item_down() {
    $params = getParams();
    $item_uuid = $_GET['itemid'];
    $label = $_GET['itemlabel'];
    $uuid = $params['uuid'];

    if (isset($_GET['gid'])) {
        $type = 'group';
        $gid = $params['gid'];
        $ret = xmlrpc_moveItemDownInMenu($gid, $type, $item_uuid);
    } else {
        $type = '';
        $uuid = $params['uuid'];
        $ret = xmlrpc_moveItemDownInMenu($uuid, $type, $item_uuid);
    }
    if ($ret) {
    /* insert notification code here if needed */
    } else {
        $str = sprintf(_T("Failed to move item <strong>%s</strong> in the boot menu", "imaging"), urldecode($label));
        new NotifyWidgetFailure($str);
    }

    header("Location: " . urlStrRedirect("base/computers/".$type."imgtabs", $params));
}

function item_edit() {

    $params = getParams();
    $item_uuid = $_GET['itemid'];
    $label = urldecode($_GET['itemlabel']);

    $item = xmlrpc_getMenuItemByUUID($item_uuid);

    if(count($_POST) == 0) {

        $name = (isset($item['boot_service']) ? $item['boot_service']['default_name'] : $item['image']['default_name']);
        printf("<h3>"._T("Edition of item", "imaging")." : <em>%s</em></h3>", $name);

        $is_selected = '';
        $is_displayed = 'CHECKED';
        $is_wol_selected = '';
        $is_wol_displayed = 'CHECKED';
        // get current values
        if($item['default'] == true)
            $is_selected = 'CHECKED';
        if($item['hidden'] == true)
            $is_displayed = '';
        if($item['default_WOL'] == true)
            $is_wol_selected = 'CHECKED';
        if($item['hidden_WOL'] == true)
            $is_wol_displayed = '';

        $f = new ValidatingForm();
        $f->push(new Table());
        $f->add(new HiddenTpl("itemid"),                        array("value" => $item_uuid,                     "hide" => True));
        $f->add(new HiddenTpl("itemlabel"),                     array("value" => $label,                         "hide" => True));
        $f->add(new HiddenTpl("gid"),                           array("value" => $_GET['gid'],                   "hide" => True));
        $f->add(new HiddenTpl("uuid"),                          array("value" => $_GET['uuid'],                  "hide" => True));
        $f->add(new HiddenTpl("default_name"),                  array("value" => $name,                          "hide" => True));

        $f->add(
            new TrFormElement(_T("Selected by default", "imaging"),
            new CheckboxTpl("default")),
            array("value" => $is_selected)
        );
        $f->add(
            new TrFormElement(_T("Displayed", "imaging"),
            new CheckboxTpl("displayed")),
            array("value" => $is_displayed)
        );
        $f->add(
            new TrFormElement(_T("Selected by default on WOL", "imaging"),
            new CheckboxTpl("default_WOL")),
            array("value" => $is_wol_selected)
        );
        $f->add(
            new TrFormElement(_T("Displayed on WOL", "imaging"),
            new CheckboxTpl("displayed_WOL")),
            array("value" => $is_wol_displayed)
        );
        $f->pop();
        $f->addButton("bvalid", _T("Validate"));
        $f->pop();
        $f->display();
    } else {
        // set new values
        if(isset($_GET['gid'])) {
            $type = 'group';
            $target_uuid = $_GET['gid'];
        } else {
            $type = '';
            $target_uuid = $_GET['uuid'];
        }

        $bs_uuid = $item['boot_service']['imaging_uuid'];
        $im_uuid = $item['image']['imaging_uuid'];

        $params['default'] = ($_POST['default'] == 'on'?True:False);
        $params['default_WOL'] = ($_POST['default_WOL'] == 'on'?True:False);
        $params['hidden'] = ($_POST['displayed'] == 'on'?False:True);
        $params['hidden_WOL'] = ($_POST['displayed_WOL'] == 'on'?False:True);
        $params['default_name'] = $_POST['default_name'];

        if (isset($bs_uuid) && $bs_uuid != '') {
            $ret = xmlrpc_editServiceToTarget($bs_uuid, $target_uuid, $params, $type);
        } else {
            $ret = xmlrpc_editImageToTarget($im_uuid, $target_uuid, $params, $type);
        }

        // goto menu boot list
        header("Location: " . urlStrRedirect("base/computers/".$type."imgtabs", $params));
    }
}

function item_list() {

    if(isset($_GET['gid'])) {
        $type = 'group';
        list($count, $menu) = xmlrpc_getProfileBootMenu($_GET['gid']);
    } else {
        $type = '';
        list($count, $menu) = xmlrpc_getComputerBootMenu($_GET['uuid']);
    }

    $params = getParams();

    // forge params
    $upAction = new ActionItem(_T("Move Up"), $type."imgtabs", "up", "item", "base", "computers", $type."tabbootmenu", "up");
    $downAction = new ActionItem(_T("Move down"), $type."imgtabs", "down", "item", "base", "computers", $type."tabbootmenu", "down");
    $editAction = new ActionItem(_T("Edit"), $type."imgtabs", "edit", "item", "base", "computers", $type."tabbootmenu", "edit");
    $deleteAction = new ActionPopupItem(_T("Delete"), "bootmenu_remove", "delete", "item", "base", "computers", $type."tabbootmenu", 300, "delete");

    $emptyAction = new EmptyActionItem();
    $actionUp = array();
    $actionDown = array();
    $actionEdit = array();
    $actionDelete = array();

    $nbItems = $count;

    $a_label = array();
    $a_desc = array();
    $a_default = array();
    $a_display = array();
    $a_defaultWOL = array();
    $a_displayWOL = array();
    $params['from'] = 'tabbootmenu';

    $i = -1;
    $root_len = 0;
    foreach ($menu as $entry) {
        $i = $i + 1;
        $is_image = False;
        if (isset($entry['image'])) {
            $is_image = True;
        }

        if ($is_image) { # TODO $entry has now a cache for desc.
            $a_desc[] = $entry['image']['desc'];
            $entry['default_name'] = $entry['image']['name'];
            $kind = 'IM';
            if ($entry['read_only']) {
                $url = '<img src="modules/imaging/graph/images/imaging-action-ro.png" style="vertical-align: middle" alt="'._T('master from the profile', 'imaging').'"/> ';
            } else {
                $url = '<img src="modules/imaging/graph/images/imaging-action.png" style="vertical-align: middle" alt="'._T('master', 'imaging').'"/> ';
            }
        } else {
            $a_desc[] = $entry['boot_service']['default_desc'];
            $entry['default_name'] = $entry['boot_service']['default_name'];
            $kind = 'BS';
            if ($entry['read_only']) {
                $url = '<img src="modules/imaging/graph/images/service-action-ro.png" style="vertical-align: middle" alt="'._T('boot service from profile', 'imaging').'"/> ';
            } else {
                $url = '<img src="modules/imaging/graph/images/service-action.png" style="vertical-align: middle" alt="'._T('boot service', 'imaging').'"/> ';
            }
        }

        $list_params[$i] = $params;
        $list_params[$i]["itemid"] = $entry['imaging_uuid'];
        $list_params[$i]["itemlabel"] = urlencode($entry['default_name']);

        if ($entry['read_only']) {
            $actionsDown[] = $emptyAction;
            $actionsUp[] = $emptyAction;
            $root_len += 1;
            $actionEdit[] = $emptyAction;
            $actionDelete[] = $emptyAction;
        } else {
            $actionEdit[] = $editAction;
            $actionDelete[] = $deleteAction;
            if ($i == $root_len) {
                if ($count == 1 || $root_len == $count - 1) {
                    $actionsDown[] = $emptyAction;
                    $actionsUp[] = $emptyAction;
                } else {
                    $actionsDown[] = $downAction;
                    $actionsUp[] = $emptyAction;
                }
            } elseif ($i > $root_len && $i == $nbItems-1) {
                $actionsDown[] = $emptyAction;
                $actionsUp[] = $upAction;
            } elseif ($i > $root_len) {
                $actionsDown[] = $downAction;
                $actionsUp[] = $upAction;
            }
        }

        $a_label[] = sprintf("%s%s", $url, $entry['default_name']); # should be replaced by the label in the good language
        $a_default[] = $entry['default'];
        $a_display[] = ($entry['hidden'] ? False:True);
        $a_defaultWOL[] = $entry['default_WOL'];
        $a_displayWOL[] = ($entry['hidden_WOL'] ? False:True);
    }
    $firstp = "<p>" . _T("\"Preselected choice\" and \"Preselected choice on WOL\" values will be used to set the default imaging client menu item to run, if no choice is made by the user on the client side prior to the menu timeout.", "imaging") . "</p>";
    /* Build tooltip text on column name */
    if ($type == "") {
        $text = $firstp . "<p>" . _T("Once the operation triggered by a choice is successfull, the preselected choice will default to the first item of the boot menu.", "imaging") . "</p>";
    } else {
        $text = $firstp . "<p>" . _T("When you modify the \"Preselected choice\" or \"Preselected choice on WOL\" values on a profile, those values will be set on all the boot menu of the computers owned by the profile.", "imaging") . "</p>" . "<p>" . _T("Then for each computer, once the operation triggered by a choice is successfull, the preselected choice will default to the first item of the boot menu.", "imaging") . "</p>";
    }
    $l = new ListInfos($a_label, _T("Label"));
    $l->setParamInfo($list_params);
    $l->addExtraInfo($a_desc, _T("Description", "imaging"));
    $l->addExtraInfo($a_default, _T("Preselected choice", "imaging")
                     , "", $text);
    $l->addExtraInfo($a_display, _T("Displayed", "imaging"));
    $l->addExtraInfo($a_defaultWOL, _T("Preselected choice on WOL", "imaging")
                     , "", $text);
    $l->addExtraInfo($a_displayWOL, _T("Displayed on WOL", "imaging"));
    $l->addActionItemArray($actionsUp);
    $l->addActionItemArray($actionsDown);
    $l->addActionItemArray($actionEdit);
    if ($count > 1) {
        $l->addActionItemArray($actionDelete);
    }
    $l->disableFirstColumnActionLink();
    $l->setTableHeaderPadding(19);
    $l->display();
}

if (($type == '' && (xmlrpc_isComputerRegistered($target_uuid) || xmlrpc_isComputerInProfileRegistered($target_uuid))) || ($type == 'group' && xmlrpc_isProfileRegistered($target_uuid)))  {
    if (isset($_GET['mod'])) {
        $mod = $_GET['mod'];
    } else {
        $mod = "none";
    }

    switch($mod) {
        case 'up':
            item_up();
            break;
        case 'down':
            item_down();
            break;
        case 'edit':
            item_edit();
            break;
        default:
            item_list();
            break;
    }
} else {
    # register the target (computer or profile)
    $params = array('target_uuid'=>$target_uuid, 'type'=>$type, 'from'=>"services", "target_name"=>$target_name);
    header("Location: " . urlStrRedirect("base/computers/".$type."register_target", $params));
}

?>

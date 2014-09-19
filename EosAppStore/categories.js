// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Lang = imports.lang;

const DEFAULT_APP_CATEGORY = 'education';

function get_app_categories() {
    return [
        {
            name: 'education',
            widget: null,
            label: _("Education"),
            id: EosAppStorePrivate.AppCategory.EDUCATION,
        },
        {
            name: 'games',
            widget: null,
            label: _("Games"),
            id: EosAppStorePrivate.AppCategory.GAMES,
        },
        {
            name: 'resources',
            widget: null,
            label: _("Resources"),
            id: EosAppStorePrivate.AppCategory.RESOURCES,
        },
        {
            name: 'utilities',
            widget: null,
            label: _("Utilities"),
            id: EosAppStorePrivate.AppCategory.UTILITIES,
        },
        {
            name: 'installed',
            widget: null,
            label: _("Installed"),
            id: EosAppStorePrivate.AppCategory.INSTALLED,
        },
    ];
}

function get_link_categories() {
    return [
        {
            name: 'news',
            widget: null,
            label: _("News"),
            id: EosAppStorePrivate.LinkCategory.NEWS,
        },
        {
            name: 'sports',
            widget: null,
            label: _("Sports"),
            id: EosAppStorePrivate.LinkCategory.SPORTS,
        },
        {
            name: 'education',
            widget: null,
            label: _("Education and Health"),
            id: EosAppStorePrivate.LinkCategory.EDUCATION,
        },
        {
            name: 'entertainment',
            widget: null,
            label: _("Entertainment"),
            id: EosAppStorePrivate.LinkCategory.ENTERTAINMENT,
        },
        {
            name: 'local',
            widget: null,
            label: _("Local"),
            id: EosAppStorePrivate.LinkCategory.LOCAL,
        }
    ];
}

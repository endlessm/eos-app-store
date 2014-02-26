// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Lang = imports.lang;

function get_app_categories() {
    return [
        {
            name: 'education',
            widget: null,
            label: _("Education"),
            id: EosAppStorePrivate.AppCategory.EDUCATION,
        },
        {
            name: 'leisure',
            widget: null,
            label: _("Leisure"),
            id: EosAppStorePrivate.AppCategory.LEISURE,
        },
        {
            name: 'utilities',
            widget: null,
            label: _("Utilities"),
            id: EosAppStorePrivate.AppCategory.UTILITIES,
        },
        {
            name: 'my-applications',
            widget: null,
            label: _("My applications"),
            id: EosAppStorePrivate.AppCategory.MY_APPLICATIONS,
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

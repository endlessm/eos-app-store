// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const EosAppStorePrivate = imports.gi.EosAppStorePrivate;
const Lang = imports.lang;

const DEFAULT_APP_CATEGORY = 'web';

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

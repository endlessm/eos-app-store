const Gtk = imports.gi.Gtk;

const Lang = imports.lang;

const defaultParams = {
    templateRoot: null,
    bindChildren: false,
    connectSignals: false,
};

function _initTemplate(params) {
    if ('_compositeChildren' in this) {
        throw new Error("composeChildren() can only be called once");        
    }

    if (!params) {
        params = {};
    }

    for (let p in defaultParams) {
        if (!(p in params)) {
            params[p] = defaultParams[p];
        }
    }

    let uiResource = Object.getPrototypeOf(this).templateResource;
    if (!uiResource) {
        throw new Error("templateResource is not defined on this instance");
    }

    let builder = new Gtk.Builder();

    try {
        if (params.templateRoot) {
            builder.add_objects_from_resource(uiResource, [ params.templateRoot ]);
        }
        else {
            builder.add_from_resource(uiResource);
        }
    }
    catch (e) {
        logError(e, 'error while loading UI resource ' + uiResource);
    }

    this._compositeChildren = [];

    let children = Object.getPrototypeOf(this).templateChildren;
    for (let i in children) {
        let name = children[i];
        this._compositeChildren[name] = builder.get_object(name);

        if (params.bindChildren) {
            let sanitized_name = name.replace(/-/g, '_');

            this[sanitized_name] = this._compositeChildren[name];
        }
    }

    if (params.connectSignals) {
        builder.connect_signals_full(Lang.bind(this,
            function(builder, object, signal, handler) {
                if (typeof(this[handler]) === 'function') {
                    object.connect(signal, Lang.bind(this, this[handler]));
                }
            }));
    }
}

function _getTemplateChild(child_name) {
    if ('_compositeChildren' in this) {
        return this._compositeChildren[child_name];
    }

    return null;
}

function bindTemplateChildren(proto) {
    if (!proto.templateResource || typeof(proto.templateResource) !== 'string') {
        throw new Error("When binding children the prototype must contain a 'templateResource' string element");
    }

    if (!proto.templateChildren || typeof(proto.templateChildren) != 'object') {
        throw new Error("When binding children the prototype must contain a 'templateChildren' array element");
    }

    proto.initTemplate = _initTemplate
    proto.getTemplateChild = _getTemplateChild;
}

;(function (define) {
    'use strict';
    define(['teams/js/collections/base', 'teams/js/models/team', 'gettext'],
        function(BaseCollection, TeamModel, gettext) {
            var TeamCollection = BaseCollection.extend({
                model: TeamModel,
                
                state: {
                    sortKey: 'last_activity_at'
                },

                queryParams: {
                    topic_id: function () {
                        return this.options.topic_id;
                    },
                    expand: 'user',
                    course_id: function () {
                        return encodeURIComponent(this.options.course_id);
                    },
                    order_by: function () {
                        return this.options.searchString ? '' : this.sortField;
                    }
                },

                constructor: function(teams, options) {
                    BaseCollection.prototype.constructor.call(this, teams, options);

                    this.registerSortableField('last_activity_at', gettext('last activity'));
                    this.registerSortableField('open_slots', gettext('open slots'));
                }
            });
            return TeamCollection;
        });
}).call(this, define || RequireJS.define);

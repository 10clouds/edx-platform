;(function (define) {
    'use strict';
    define(['paging-collection'],
        function(PagingCollection) {
            var BaseCollection = PagingCollection.extend({
                constructor: function (models, options) {
                    this.options = options;
                    this.url = options.url;
                    this.state.perPage = options.per_page;

                    this.course_id = options.course_id;
                    this.teamEvents = options.teamEvents;
                    this.teamEvents.bind('teams:update', this.onUpdate, this);
                    
                    PagingCollection.prototype.constructor.call(this, models, options);
                },

                parse: function (response, options) {
                    if (!response) {
                        response = {};
                    }

                    if (!response.results) {
                        response.results = [];
                    }

                    return PagingCollection.prototype.parse.call(this, response, options);
                },

                onUpdate: function(event) {
                    // Mark the collection as stale so that it knows to refresh when needed.
                    this.isStale = true;
                }
            });
            return BaseCollection;
        });
}).call(this, define || RequireJS.define);

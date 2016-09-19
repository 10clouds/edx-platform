/**
 * Entry point for the subscription flow.
 *
 * We pass some information to the base view
 * using "data-" attributes on the parent div.
 * See "pay.html" for the exact attribute names.
 *
 */
var edx = edx || {};

(function( $, _ ) {
    'use strict';
    var errorView,
        el = $('#subscription-container');

    edx.subscription = edx.subscription || {};

    // Initialize an error view for displaying top-level error messages.
    errorView = new edx.subscription.ErrorView({
        el: $('#error-container')
    });

    // Initialize the base view, passing in information
    // from the data attributes on the parent div.
    //
    // The data attributes capture information that only
    // the server knows about, such as the course and course mode info,
    // full URL paths to static underscore templates,
    // and some messaging.
    //
    return new edx.subscription.PayView({
        errorModel: errorView.model,
        subscriptionData: {
            isActive: el.data('is-active'),
            courseKey: el.data('course-key'),
            courseName: el.data('course-name'),
            minPrice: el.data('course-mode-min-price'),
            sku: el.data('course-mode-sku'),
            currency: el.data('course-mode-currency'),
            processors: el.data('processors'),
            courseModeSlug: el.data('course-mode-slug')
        }
    }).render();
})( jQuery, _ );

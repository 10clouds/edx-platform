/**
 * Base view for the payment flow.
 *
 */
var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.subscription = edx.subscription || {};

    edx.subscription.PayView = Backbone.View.extend({
        el: '#subscription-container',
        templateName: "make_payment_step",
        btnClass: 'action-primary',

        initialize: function( obj ) {
            this.errorModel = obj.errorModel || null;
            this.courseKey = obj.courseKey || null;
            this.stepData = obj.subscriptionData;
        },

        render: function() {
            var stepView, stepEl;

            // Get or create the step container
            stepEl = $("#current-step-container");
            if (!stepEl.length) {
                stepEl = $('<div id="current-step-container"></div>').appendTo(this.el);
            }

            var templateHtml = $( "#" + this.templateName + "-tpl" ).html();
            // Allow subclasses to add additional information
            // to the template context, perhaps asynchronously.
            this.updateContext( this.templateContext() ).done(
                function( templateContext ) {
                    // Render the template into the DOM
                    $( this.el ).html( _.template( templateHtml, templateContext ) );

                    // Allow subclasses to install custom event handlers
                    this.postRender();
                }
            ).fail( _.bind( this.handleError, this ) );

            return this;
        },

        handleError: function( errorTitle, errorMsg ) {
            this.errorModel.set({
                errorTitle: errorTitle || gettext( "Error" ),
                errorMsg: errorMsg || gettext( "An error has occurred. Please try reloading the page." ),
                shown: true
            });
        },

        templateContext: function() {
            return _.extend( this.defaultContext(), this.stepData );
        },

        updateContext: function( templateContext ) {
            var view = this;
            return $.Deferred(
                function( defer ) {
                    defer.resolveWith( view, [ templateContext ]);
                }
            ).promise();
        },

        defaultContext: function() {
            return {
                isActive: true,
                minPrice: 0,
                sku: '',
                currency: 'usd',
                courseName: '',
                platformName: '',
                alreadyVerified: false,
                courseModeSlug: 'audit'
            };
        },

        _getPaymentButtonText: function(processorName) {
            if (processorName.toLowerCase().substr(0, 11)=='cybersource') {
                return gettext('Checkout');
            } else if (processorName.toLowerCase()=='paypal') {
                return gettext('Pay with PayPal');
            } else if (processorName.toLowerCase()=='braintree') {
                return gettext('Credit Card');
            } else {
                // This is mainly for testing as no other processors are supported right now.
                // Translators: 'processor' is the name of a third-party payment processing vendor (example: "PayPal")
                return interpolate_text(gettext('Pay with {processor}'), {processor: processorName});
            }
        },

        _getPaymentButtonHtml: function(processorName) {
            var self = this;
            return _.template(
                '<button class="next <%- btnClass %> payment-button" id="<%- name %>" ><%- text %></button> '
            )({name: processorName, text: self._getPaymentButtonText(processorName), btnClass: this.btnClass});
        },

        postRender: function() {
            var templateContext = this.templateContext(),
                processors = templateContext.processors || [],
                self = this;
            this.setPaymentEnabled( true );

            // render the name of the product being paid for
            $( 'div.payment-buttons span.product-name').append(gettext( "Subscription" ));

            if (processors.length === 0) {
                // No payment processors are enabled at the moment, so show an error message
                this.errorModel.set({
                    errorTitle: gettext('All payment options are currently unavailable.'),
                    errorMsg: gettext('Try the transaction again in a few minutes.'),
                    shown: true
                })
            }
            else {
                // create a button for each payment processor
                _.each(processors.reverse(), function(processorName) {
                    $( 'div.payment-buttons' ).append( self._getPaymentButtonHtml(processorName) );
                });
            }

            // Handle payment submission
            $( '.payment-button' ).on( 'click', _.bind( this.createOrder, this ) );
        },

        setPaymentEnabled: function( isEnabled ) {
            if ( _.isUndefined( isEnabled ) ) {
                isEnabled = true;
            }
            $( '.payment-button' )
                .toggleClass( 'is-disabled', !isEnabled )
                .prop( 'disabled', !isEnabled )
                .attr('aria-disabled', !isEnabled);
        },

        // This function invokes the create_order endpoint.  It will either create an order in
        // the lms' shoppingcart or a basket in Otto, depending on which backend the request course
        // mode is configured to use.  In either case, the checkout process will be triggered,
        // and the expected response will consist of an appropriate payment processor endpoint for
        // redirection, along with parameters to be passed along in the request.
        createOrder: function(event) {
            var paymentAmount = this.templateContext().minPrice,
                postData = {
                    'processor': event.target.id,
                    'contribution': paymentAmount,
                    'course_id': this.stepData.courseKey,
                    'sku': this.templateContext().sku
                };

            // Disable the payment button to prevent multiple submissions
            this.setPaymentEnabled( false );

            $( event.target ).toggleClass( 'is-selected' );

            // Create the order for the amount
            $.ajax({
                url: '/verify_student/create_order/',
                type: 'POST',
                headers: {
                    'X-CSRFToken': $.cookie('csrftoken')
                },
                data: postData,
                context: this,
                success: this.handleCreateOrderResponse,
                error: this.handleCreateOrderError
            });

        },

        handleCreateOrderResponse: function( paymentData ) {
            // At this point, the basket has been created on the server,
            // and we've received signed payment parameters.
            // We need to dynamically construct a form using
            // these parameters, then submit it to the payment processor.
            // This will send the user to an externally-hosted page
            // where she can proceed with payment.
            var form = $( '#payment-processor-form' );

            $( 'input', form ).remove();

            form.attr( 'action', paymentData.payment_page_url );
            form.attr( 'method', 'POST' );

            _.each( paymentData.payment_form_data, function( value, key ) {
                $('<input>').attr({
                    type: 'hidden',
                    name: key,
                    value: value
                }).appendTo(form);
            });

            // Marketing needs a way to tell the difference between users
            // leaving for the payment processor and users dropping off on
            // this page. A virtual pageview can be used to do this.
            window.analytics.page( 'payment', 'payment_processor_step' );

            this.submitForm( form );
        },

        handleCreateOrderError: function( xhr ) {
            var errorMsg = gettext( 'An error has occurred. Please try again.' );

            if ( xhr.status === 400 ) {
                errorMsg = xhr.responseText;
            }

            this.errorModel.set({
                errorTitle: gettext( 'Could not submit order' ),
                errorMsg: errorMsg,
                shown: true
            });

            // Re-enable the button so the user can re-try
            this.setPaymentEnabled( true );

            $( '.payment-button' ).toggleClass( 'is-selected', false );
        },

        // Stubbed out in tests
        submitForm: function( form ) {
            form.submit();
        }
    });

})(jQuery, _, Backbone, gettext);

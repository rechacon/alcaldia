odoo.define('pragmatic_odoo_whatsapp_integration.pos', function (require) {
    'use strict';

    const { Printer } = require('point_of_sale.Printer');
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const { Gui } = require('point_of_sale.Gui');


    const WhatsappPOSReceiptScreen = (ReceiptScreen) =>
        class extends ReceiptScreen {
            constructor() {
                super(...arguments);
                useListener('click-whatsapp-send-text-receipt', (event) => this._js_custom_print());
            }

        async _js_custom_print() {
        var order = this.env.pos.get_order();
        var order_list = this.env.pos.get_order_list();
        var client = order.get_client();

        // Render receipt screen and can print function
        if (client){
        var value = {
            'order': order.name,
            'formatted_validation_date': order.formatted_validation_date,
            'company_name': this.env.pos.company.name,
            'company_phone': this.env.pos.company.phone,
            'user_name': this.env.pos.user.name,
//            'order_lines': order_list[0].orderlines.models
            }
             $.ajax({
                url : '/whatsapp/send/message',
                data : value,
                type: "POST",

                success: function (data) {
                    if (data == 'Send Message successfully'){
                    Gui.showPopup('ConfirmPopup', {
                            title: 'Message',
                            body: data,
                        });
                    }
                    else{
                    Gui.showPopup('ErrorPopup', {
                            title: 'Message',
                            body: data,
                        });
                    }
                    }
                });
                }
                else{
                 alert("You have not selected customer for this transaction")
                }
            }
        };
            Registries.Component.extend(ReceiptScreen, WhatsappPOSReceiptScreen);
    return WhatsappPOSReceiptScreen;

});

if (typeof jQuery === "undefined") {
    throw new Error("Carregar JQuery antes deste arquivo.");
}

$.Admin = {};

//Formsets
$.Admin.formset = {
    init: function() {
        var _this = this;
        var $formset_box = $('.formset-box');

        $formset_box.each(function(){
            var currentBox = $(this);
            var formsetPrefix = currentBox.find('.formset:last').prop('id');
            var nFormsets = (parseInt(formsetPrefix.substring(formsetPrefix.indexOf('-') + 1), 10) + 1).toString();

            formsetPrefix = formsetPrefix.substring(0, formsetPrefix.indexOf('-'));

            //Esconder campo DELETE do Django
            currentBox.find('.formset').each(function(){
                _this.hideDeleteField($(this))
            });

            //Esconder botao adicionar novo dos formularios, excluindo o ultimo
            currentBox.find('.formset:not(:last)').each(function(){
                $(this).find('.add-formset').hide();
            });

            //Adicionar novo formset
            currentBox.on('click', '.add-formset', function(e){
                e.preventDefault();
                var parentFormset = $(this).parents('.formset');
                _this.createNewForm(parentFormset, nFormsets);

                //Adicionar form ao manager
                nFormsets++;
                $('#id_' + formsetPrefix + '-TOTAL_FORMS').val(nFormsets);

                //Esconder add e remove do penultimo form
                $(this).hide();
                parentFormset.next().trigger('formCreated');
            });

            //Remover formset
            currentBox.on('click', '.remove-formset', function(e){
                e.preventDefault();
                var parentFormset = $(this).parents('.formset');
                var entryId = parentFormset.find('input:hidden[id $="-id"],input:hidden[id $="grupo_ptr"]');

                if(entryId.length){
                    parentFormset.find('input:checkbox[id $="-DELETE"]').prop('checked', true);
                }else{
                    parentFormset.find(':input').each(function(){
                        $(this).prop({'value': ''}).val('').prop('checked',false);
                    });
                    parentFormset.find('input:checkbox[id $="-DELETE"]').prop('checked', true);
                    parentFormset.trigger('newFormRemoved');
                }
                parentFormset.hide().change();

                var addBtn = currentBox.find('.formset:visible:last .add-formset');

                if(!addBtn.length){
                    _this.createNewForm(parentFormset, nFormsets);
                    //Adicionar form ao manager
                    nFormsets++;
                    $('#id_' + formsetPrefix + '-TOTAL_FORMS').val(nFormsets);
                }else{
                    addBtn.show();
                }

                parentFormset.trigger('formRemoved');
            });
        });
    },

    hideDeleteField: function(formset){
        var delete_input = formset.find('input:checkbox[id $="-DELETE"]');
        var delete_td = delete_input.parent('.field-td');

        delete_input.parents('.form-group:first').parent('div').hide();

        delete_td.closest('table').find('th').eq(delete_td.index()).hide();
        delete_td.hide();
    },

    createNewForm: function(parentFormset, nFormsets){
        var newForm = parentFormset.clone(true);

        //Trocar id
        var nameRegex = /-\d+-?/g;
        var newId = newForm.prop('id').replace(nameRegex, '-' + (nFormsets));
        newForm.prop({'id':newId});

        //Trocar names e ids dos inputs
        newForm.find(':input').each(function(){
            var newName = $(this).prop('name');
            if($(this).prop('type') == 'hidden'){
                $(this).remove();
            }
            //Remover mask do clone, senao nao funciona com novos inputs!
            $(this).removeData('mask');

            if(newName){
                newName = newName.replace(nameRegex, '-' + (nFormsets) + '-');
                var newId = 'id_' + newName;
                $(this).prop({'name': newName, 'id': newId, 'value': ''}).val('');

                if($(this).prop('type') == 'checkbox'){
                    $(this).prop({'checked': false}).removeProp('value').removeAttr('value');
                }
            }

        });

        //Trocar atributos for dos labels
        newForm.find('label').each(function() {
            var newFor = $(this).prop('for');
            if(newFor){
                newFor = newFor.replace(nameRegex,'-' + nFormsets + '-');
                $(this).prop({'for': newFor});
            }

            if($(this).hasClass('error')){
                $(this).remove();
            }
        });
        newForm.show();
        newForm.insertAfter(parentFormset);
    },

    createNewTrForms: function(table, n_new_forms){
        var startFrom = 0;
        table.find('tbody tr').each(function(){
            var table_row = $(this);
            var entryId = table_row.find('input:hidden[id $="-id"]');

            if(entryId.length){
                table_row.find('input:checkbox[id $="-DELETE"]').prop('checked', true);
                startFrom++;
                table_row.addClass('hidden');
            }else{
                table_row.remove();
            }
        });

        if(typeof n_new_forms != 'undefined' || n_new_forms){
            var formsetPrefix = table.find('tbody tr').eq(0).prop('id');
            formsetPrefix = formsetPrefix.substring(0, formsetPrefix.indexOf('-'));

            for (i = 0; i < parseInt(n_new_forms); i++) {
                if(startFrom <= 0){
                    var trClones = table.find('tbody tr').eq(0).removeClass('hidden').clone(true);
                }else{
                    var trClones = table.find('tbody tr').eq(startFrom-1).clone(true);
                    trClones.removeClass('hidden');
                }

                var nameRegex = /-\d+-?/g;

                trClones.each(function(){
                    var nameIdNumber = i + startFrom;
                    var newId = $(this).prop('id').replace(nameRegex, '-' + (nameIdNumber));

                    $(this).prop({'id':newId});

                    $(this).find('input').each(function(){
                        var newName = $(this).prop('name');
                        if($(this).prop('type') == 'hidden'){
                            $(this).remove();
                        }

                        //Remover mask do clone, senao nao funciona com novos inputs!
                        $(this).removeData('mask');
                        //Desfazer datepicker
                        if($(this).hasClass('datepicker')){
                            $(this).datepicker('destroy').removeAttr('id').removeProp('id');
                        }

                        if(newName){
                            newName = newName.replace(nameRegex, '-' + (nameIdNumber) + '-');
                            var newId = 'id_' + newName;
                            $(this).prop({'name': newName, 'id': newId, 'value': ''}).val('').prop('checked',false);
                        }
                    });

                    $(this).appendTo(table.find('tbody'));
                });
            }

            //Adicionar form ao manager
            $('#id_' + formsetPrefix + '-TOTAL_FORMS').val(parseInt(n_new_forms) + startFrom);
        }
    },
}


$(function () {
    $.Admin.formset.init();
});
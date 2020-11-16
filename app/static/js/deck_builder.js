function update_counts() {
  let creatures = $('#maindeckCreatures li').length
  let land = $('#maindeckOther li.card-type-land').length
  let other = $('#maindeckOther li').length - land

  var basic_land = 0
  $('.basic-count').each(function (i, elem) {
    basic_land += parseInt($(elem).text())
  })

  let total = creatures + other + land + basic_land

  $('#countMaindeck').text(total)
  $('#countCreatures').text(creatures)
  $('#countOther').text(other)
  $('#countLands').text(land + basic_land)
}

function basic_land_adjust() {
  let button = $(this)
  let parent = button.parent('.basic-selector')

  let diff = button.hasClass('basic-add') ? 1 : -1
  let count_span = parent.find('.basic-count')
  let count = Math.max(0, parseInt(count_span.text()) + diff)

  count_span.text(count)

  update_counts()
}

function build_deck_data() {
  let maindeck = $('#maindeck .card-list-item').map(function() {
    return $(this).data('card-id')
  }).get()

  let sideboard = $('#sideboard .card-list-item').map(function() {
    return $(this).data('card-id')
  }).get()

  let basics = $('.basic-selector').map(function() {
    let sel = $(this)
    let land = sel.find('.basic-type').text()
    let count = sel.find('.basic-count').text()
    return count + ' ' + land
  }).get()

  return {
    maindeck: maindeck,
    sideboard: sideboard,
    basics: basics
  }

}

function swap_maindeck_sideboard() {
  let li = $(this)
  let row = li.closest('#maindeck,#sideboard')
  let section = li.closest('.creature-row,.other-row')
  let col_header = li.parent().siblings('div').first().find('.deckbuilder-col-header').text()

  var new_row;
  if (row.attr('id') == 'maindeck') {
    new_row = row.siblings('#sideboard')
  }
  else {
    new_row = row.siblings('#maindeck')
  }

  var new_section;
  if (section.hasClass('creature-row')) {
    new_section = new_row.find('.creature-row')
  }
  else {
    new_section = new_row.find('.other-row')
  }

  let new_col = new_section.find('p:contains('+col_header+')').parent().siblings('ul').first()

  li.detach()
  li.appendTo(new_col)
  update_counts()
}

$(document).ready(function() {

  // Initialization
  update_counts()
  autocard_init('card-list-item')

  // Make the cards movable.
  $(".sortable").sortable({
    connectWith: '.card-list',
    placeholder: 'sortable-highlight',
    start: function(e, ui){
      ui.placeholder.height(ui.item.height())
    },
    stop: update_counts
  })
  $( ".sortable" ).disableSelection()

  // Use double-click to swap between maindeck and sideboard
  $('.card-list-item').dblclick(swap_maindeck_sideboard)

  // Basic Land Selectors
  $('.basic-adjust').click(basic_land_adjust)
  $('.basic-selector').disableSelection()

  // Save the deck
  $("#saveLink").click(function() {
    $.ajax({
      type: 'POST',
      url: $('#saveMeta').data('save-url'),
      data: JSON.stringify(build_deck_data()),
      contentType: "application/json; charset=utf-8",
      success: function() {
        let msg_template = $('#messageTemplate').clone()
        msg_template.removeAttr('id')
        msg_template.removeClass('d-none')
        msg_template.find('p').text('Deck Saved')
        $('#flashMessages').append(msg_template)
      },
      error: function(error_message) {
        let msg_template = $('#messageTemplate').clone()
        msg_template.removeAttr('id')
        msg_template.removeClass('d-none')
        msg_template.removeClass('alert-success')
        msg_template.addClass('alert-danger')
        msg_template.find('p').text('Error: ' + error_message)
        console.log(error_message)
        $('#flashMessages').append(msg_template)
      }
    })
  })
})

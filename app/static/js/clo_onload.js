document.addEventListener("DOMContentLoaded", function() {
  function init_card_frames() {
     $('.closeup-card-wrapper').each(function() {
       const elem = $(this)
       const card_id = elem.data('card-id')
       if (!card_id) {
         return
       }

       const data = window.clo.card_data[card_id]
       if (!data) {
         console.log(card_id)
         return
       }

       clo.util.draw_card_frame(elem, data)
     })
  }

  function init_card_line_items() {
    $('.clo-card').each(function(index, e) {
      const elem = $(e)
      const card_id = elem.data('card-id')
      if (!card_id) {
        return
      }

      const data = window.clo.card_data[card_id]
      const front = data['card_faces'][0]
      const back = data['card_faces'][1]

      elem.attr('data-front', front['art_crop_url'])
      if (back) {
        elem.attr('data-back', back['art_crop_url'])
      }

      elem.text(data['name'])

      if (front.achievements) {
        const ach_elem = $('<i class="fab fa-font-awesome-flag">')
        elem.prepend(ach_elem)
      }

      if (front.scarred || (back && back.scarred)) {
        const scar_elem = $('<i class="fas fa-bolt">')
        elem.prepend(scar_elem)
      }

      if (front.mana_cost) {
        const mana_elem = $('<div class="card-mana-cost" style="float: right; font-size: .6rem;">')
        mana_elem.append(clo.util.mana_symbols_from_string(front.mana_cost))
        elem.prepend(mana_elem)
      }
    })
  }

  init_card_frames()
  init_card_line_items()
})

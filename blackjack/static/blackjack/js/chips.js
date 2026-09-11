/*
 * Lets a chip stack in the pit/purse be dragged into the other zone as a
 * shortcut for clicking it. htmx swaps #table's innerHTML on every action,
 * which would silently detach any listener bound directly to a chip, so
 * everything here is delegated off `document` and re-queries the DOM at
 * click/drag/drop time.
 *
 * Clicking (or dropping) a chip normally moves one coin. Betting a big pile
 * of $1 chips one click at a time is tedious, so a modifier key bumps the
 * quantity for that single click: shift moves 5, shift+ctrl/cmd moves the
 * whole stack (bet_coin/unbet_coin clamp the count to what's on hand).
 */
(function () {
    const HANDFUL = 5;
    const WHOLE_STACK = 1000000;

    function dropZone(target) {
        return target.closest('.pit, .purse');
    }

    function quantityFor(event) {
        if (event.shiftKey && (event.ctrlKey || event.metaKey)) return WHOLE_STACK;
        if (event.shiftKey) return HANDFUL;
        return 1;
    }

    document.addEventListener('click', function (event) {
        const chip = event.target.closest('[data-chip-denom]');
        if (!chip) return;
        const countInput = chip.closest('form').querySelector('input[name="count"]');
        if (countInput) countInput.value = quantityFor(event);
    });

    document.addEventListener('dragstart', function (event) {
        const chip = event.target.closest('[data-chip-denom]');
        if (!chip) return;
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('text/plain', JSON.stringify({
            denom: chip.dataset.chipDenom,
            origin: chip.dataset.chipOrigin,
            count: quantityFor(event),
        }));
        chip.classList.add('dragging');
    });

    document.addEventListener('dragend', function (event) {
        const chip = event.target.closest('[data-chip-denom]');
        if (chip) chip.classList.remove('dragging');
    });

    document.addEventListener('dragover', function (event) {
        if (dropZone(event.target)) event.preventDefault();
    });

    document.addEventListener('dragenter', function (event) {
        const zone = dropZone(event.target);
        if (zone) zone.classList.add('drag-over');
    });

    document.addEventListener('dragleave', function (event) {
        const zone = dropZone(event.target);
        if (zone && !zone.contains(event.relatedTarget)) zone.classList.remove('drag-over');
    });

    document.addEventListener('drop', function (event) {
        const zone = dropZone(event.target);
        if (!zone) return;
        event.preventDefault();
        zone.classList.remove('drag-over');

        let payload;
        try {
            payload = JSON.parse(event.dataTransfer.getData('text/plain'));
        } catch (err) {
            return;
        }
        const targetOrigin = zone.classList.contains('pit') ? 'pit' : 'wallet';
        if (!payload.denom || payload.origin === targetOrigin) return;

        const action = targetOrigin === 'pit' ? 'bet_coin' : 'unbet_coin';
        const form = document.querySelector(
            `form[data-action="${action}"][data-denom="${payload.denom}"]`
        );
        if (!form) return;
        const countInput = form.querySelector('input[name="count"]');
        if (countInput) countInput.value = payload.count || 1;
        form.requestSubmit();
    });
})();

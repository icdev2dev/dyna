import 'svelte/internal/disclose-version';
import * as $ from 'svelte/internal/client';

const inc = (_, count) => $.set(count, $.get(count) + 1);
var root = $.from_html(`<div style="padding:8px"><h2> </h2> <p> </p> <button>Increment</button></div>`);

export default function PluginRoot($$anchor, $$props) {
	let who = $.prop($$props, 'who', 3, 'world');
	let count = $.state(0);
	var div = root();
	var h2 = $.child(div);
	var text = $.child(h2);

	$.reset(h2);

	var p = $.sibling(h2, 2);
	var text_1 = $.child(p);

	$.reset(p);

	var button = $.sibling(p, 2);

	button.__click = [inc, count];
	$.reset(div);

	$.template_effect(() => {
		$.set_text(text, `Hello, ${who() ?? ''}!`);
		$.set_text(text_1, `Count: ${$.get(count) ?? ''}`);
	});

	$.append($$anchor, div);
}

$.delegate(['click']);
import InputField from './InputField.svelte';
import SubmitButton from './SubmitButton.svelte';
import GroupField from './GroupField.svelte';

export default {
  input: InputField,
  submit: SubmitButton,
  group: GroupField, // Enables registration logic if you want `group` in registry
};

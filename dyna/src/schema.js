export default {
  type: "form",
  fields: [
    { type: "input", label: "Name", name: "name" },
    {
      type: "group",
      label: "Details",
      fields: [
        { type: "input", label: "Age", name: "age" },
        { type: "input", label: "Email", name: "email" },
      ]
    },
    { type: "submit", label: "Save" }
  ]
};

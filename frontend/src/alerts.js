import Swal from "sweetalert2";

const LilacTheme = Swal.mixin({
  confirmButtonColor: "#a678ec",
  cancelButtonColor: "#e5e3ea",
  background: "#ffffff",
  color: "#2d2a35",
  confirmButtonText: "Aceptar",
  backdrop: "rgba(247, 246, 249, 0.85)",
  customClass: {
    popup: "lilac-popup",
    title: "lilac-title",
    htmlContainer: "lilac-text",
  },
});

export const alertSuccess = (title, text = "") =>
  LilacTheme.fire({
    icon: "success",
    title,
    text,
    confirmButtonText: "Aceptar",
  });

export const alertError = (title, text = "") =>
  LilacTheme.fire({
    icon: "error",
    title,
    text,
    confirmButtonText: "Entendido",
  });

export const alertInfo = (title, text = "") =>
  LilacTheme.fire({
    icon: "info",
    title,
    text,
  });

export const confirmDialog = (title, text = "") =>
  LilacTheme.fire({
    title,
    text,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    reverseButtons: true,
  });

export default LilacTheme;

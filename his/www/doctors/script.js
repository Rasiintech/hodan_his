document.addEventListener("DOMContentLoaded", function () {
  console.log("hi")

  let currentImageIndex = 0;
  const images = [
    "/doctors/imge1.jpeg",
    "/doctors/image2.jpeg",
    "/doctors/images3.jpeg",
  ];

  function changeImage() {
    currentImageIndex = (currentImageIndex + 1) % images.length;
    const sliderImage = document.getElementById("sliderImage");
    sliderImage.classList.remove("fade");
    setTimeout(() => {
      sliderImage.src = images[currentImageIndex];
      sliderImage.classList.add("fade");
    }, 10);
  }

  setInterval(changeImage, 5000);
});

// the apis
// document.addEventListener("DOMContentLoaded", function () {
//   const baseUrl = "http://104.251.219.249";
//   const formHeader = document.querySelector(".form-container h1");
//   const appointmentButtons = document.querySelectorAll(".appointment-btn");

//   appointmentButtons.forEach((button) => {
//     button.addEventListener("click", function () {
//       const card = button.closest('div[style*="flex-direction: column;"]');
//       const doctorNameElement = card.querySelector("strong");
//       const doctorName = doctorNameElement
//         ? doctorNameElement.textContent
//         : "Doctor's name not found";

//       formHeader.textContent = `Book Appointment with ${doctorName}`;

//       document.getElementById("overlay").style.display = "block";
//       document.getElementById("appointmentForm").style.display = "block";
//     });
//   });

//   window.closeForm = function () {
//     document.getElementById("overlay").style.display = "none";
//     document.getElementById("appointmentForm").style.display = "none";
//   };
// });

// function submitForm(event) {
//   event.preventDefault();

//   const baseUrl = "http://104.251.219.249";
//   const name = document.getElementById("name").value;
//   const sex = document.getElementById("sex").value;
//   const phone = document.getElementById("phone").value;
//   const address = document.getElementById("address").value;

//   if (!name || !sex || !phone || !address) {
//     alert("Please fill all fields.");
//     return false;
//   }

//   const doctorName = document
//     .querySelector(".form-container h1")
//     .textContent.replace("Book Appointment with ", "");
//   const data = {
//     doctor_name: doctorName,
//     patient_name: name,
//     patient_sex: sex,
//     patient_phone: phone,
//     patient_address: address,
//   };

//   const options = {
//     method: "POST",
//     headers: {
//       Accept: "application/json",
//       "Content-Type": "application/json;charset=UTF-8",
//       Authorization: "token e1cfd767093e7f4:78189f296ee1310",
//     },
//     body: JSON.stringify(data),
//   };

//   console.log("Sending data to API:", data);
//   fetch(`${baseUrl}/api/method/make_appointment`, options)
//     .then((response) => {
//       if (!response.ok) {
//         throw new Error("Network response was not ok");
//       }
//       return response.json();
//     })
//     .then((responseData) => {
//       console.log("API Response:", responseData);
//       alert("Appointment booked successfully!");
//       closeForm();
//     })
//     .catch((error) => {
//       console.error("Error booking appointment:", error);
//       alert("Failed to book appointment.");
//     });

//   return false;
// }

// Doctor Cards

// document.addEventListener("DOMContentLoaded", function () {
//   fetch("http://104.251.219.249/api/method/get_doctors", {
//     method: "POST",
//     headers: {
//       Accept: "application/json",
//       "Content-Type": "application/json",
//       Authorization: "token e1cfd767093e7f4:78189f296ee1310",
//     },
//   })
//     .then((response) => {
//       if (!response.ok) throw new Error("Network response was not ok");
//       return response.json();
//     })
//     .then((responseData) => {
//       console.log("API Response:", responseData);
//     });
//   const doctors = [
//     {
//       doctor_name: "Dr. A K Yusuf",
//       registration_no: "4228",
//       languages: "English, বাংলা, हिंदी",
//       experience: "30 years",
//       location: "Canal Circular Road, Kolkata",
//     },
//     {
//       doctor_name: "Dr. abdullahi",
//       registration_no: "4229",
//       languages: "English, বাংলা, हिंदी",
//       experience: "25 years",
//       location: "New Town, Kolkata",
//     },

//     {
//       doctor_name: "Dr. A K Yasiin",
//       registration_no: "4229",
//       languages: "English, বাংলা, हिंदी",
//       experience: "25 years",
//       location: "New Town, Kolkata",
//     },
//   ];

// fix one

document.addEventListener("DOMContentLoaded", function () {
    const baseUrl = "http://104.251.219.249";
    

  const overlay = document.getElementById("overlay");
  const appointmentForm = document.getElementById("appointmentForm");
  const formHeader = appointmentForm.querySelector(".form-container h1");
  const container = document.getElementById("doctorContainer");
  const resultCount = document.getElementById("resultCount");

  // Fetch doctors' information
  fetch(baseUrl + "/api/method/get_doctors", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      Authorization: "token e1cfd767093e7f4:78189f296ee1310",
    },
  })
    .then((response) => {
      if (!response.ok) throw new Error("Network response was not ok");
      return response.json();
    })
    .then((responseData) => {
      if (!responseData.message) {
        console.error("Data not found in response:", responseData);
        return; // Stop further execution if data is not found
      }

      const doctors = responseData.message;
      console.log("doctors:-", doctors)
      resultCount.textContent = doctors.length;
      container.innerHTML = ""; // Clear existing content

      doctors.forEach((doctor) => {
        const cardHTML = `
                <div class="card"
                   style="display: flex; flex-direction: column; background-color: white; box-shadow: rgba(0, 0, 0, 0.35) 0px 5px 15px; border-radius: 6px; background-image: url('./bg.png'); background-repeat: no-repeat; background-position: right top;">
                    <div style="display: flex; gap: 19px; padding: 15px">
                        <div>
                            <img style="width: 99px; height: 99px; border-radius: 50%; object-fit: cover; object-position: center center; border: 1px solid gray;" src="./dr-cardiology.png" alt="dr-cardiology" />
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 28px">
                            <div style="display: flex; flex-direction: column; gap: 3px">
                                <strong style="font-weight: bold">${doctor.doctor_name}</strong>
                                <span style="color: gray">MBBS, MD, Dip. Card., FCCP</span>
                            </div>
                            <div style="display: flex; flex-direction: column">
                                <span style="color: gray">Languages</span>
                                <strong style="font-weight: bold">${doctor.languages}</strong>
                            </div>
                            <div style="display: flex; flex-direction: column; gap: 15px">
                                <div style="display: flex; align-items: center; gap: 8px">
                                    <img src="./award.svg" alt="award" />
                                    <span style="color: gray">${doctor.experience} experience overall</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 8px">
                                    <img src="./location.svg" alt="location" />
                                    <span style="color: gray">${doctor.location}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div style="border: 1px solid #e7eaeb; margin: 0 15px"></div>
                    <div style="display: flex; justify-content: space-between; margin: 0 15px; padding-top: 19px; padding-bottom: 19px;">
                        <div style="display: flex; flex-direction: column; gap: 3px">
                            <strong style="font-weight: bold">MON, FRI</strong>
                            <span style="color: red">(11:00 AM-12:00 PM)</span>
                        </div>
                        <button class="appointment-btn" style="text-transform: uppercase; background-color: #016a87; color: white; border: none; outline: none; border-radius: 6px; padding: 0 8px; cursor: pointer;">Book an appointment</button>
                    </div>
                </div>
            `;
        container.innerHTML += cardHTML;
      });

      attachEventListenersToButtons();
    })
    .catch((error) => {
      console.error("Error fetching doctors:", error);
    });

  // Attach event listeners to dynamically created buttons
  function attachEventListenersToButtons() {
    Array.from(document.querySelectorAll(".appointment-btn")).forEach(
      (button) => {
        button.addEventListener("click", function () {
          const doctorName =
            this.closest(".card").querySelector("strong").textContent;
          formHeader.textContent = `Book Appointment with ${doctorName}`;
          overlay.style.display = "block";
          appointmentForm.style.display = "block";
        });
      }
    );
  }

  // Function to close the form
  window.closeForm = function () {
    overlay.style.display = "none";
    appointmentForm.style.display = "none";
  };

  // Handling form submission
  appointmentForm.addEventListener("submit", function (event) {
    event.preventDefault();
    submitForm();
  });

  function submitForm() {
    const name = document.querySelector(
      "#appointmentForm input[name='name']"
    ).value;
    const sex = document.querySelector(
      "#appointmentForm select[name='sex']"
    ).value;
    const phone = document.querySelector(
      "#appointmentForm input[name='phone']"
    ).value;
    const address = document.querySelector(
      "#appointmentForm input[name='address']"
    ).value;
    const doctorName = formHeader.textContent.replace(
      "Book Appointment with ",
      ""
    );
    const phoneError = document.querySelector(
      "#appointmentForm .error-message"
    );
    // Validate phone number for Somali numbers (10 digits)
    if (!/^\d{10}$/.test(phone)) {
      phoneError.style.display = "block"; // Show error message
      return;
    } else {
      phoneError.style.display = "none"; // Hide error message
    }
    if (!name || !sex || !phone || !address) {
      alert("Please fill all fields.");
      return;
    }

    const data = {
      doctor_name: doctorName,
      patient_name: name,
      patient_sex: sex,
      patient_phone: phone,
      patient_address: address,
    };

    fetch(baseUrl + "/api/method/make_appointment", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: "token e1cfd767093e7f4:78189f296ee1310",
      },
      body: JSON.stringify(data),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((responseData) => {
        console.log("Appointment booked successfully:", responseData);
        alert("Appointment booked successfully!");
        closeForm();
      })
      .catch((error) => {
        console.error("Error booking appointment:", error);
        alert("Failed to book appointment.");
      });
  }
});

import React, { useState } from "react";
import logo from "../assets/img/logo_blanco.png";
function Navbar() {
  const [open, setOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  return (
    <div className="">
      <div className="antialiased bg-gray-100 dark:bg-gray-900">
        <div className="w-full text-gray-700 bg-white dark:text-gray-200 dark:bg-gray-800">
          <div className="flex flex-col px-4 mx-auto w-full md:items-center md:justify-between md:flex-row md:px-6 lg:px-8">
            <div className="flex flex-row items-center justify-between">
              <a
                href="#"
                className="flex item-start text-lg font-semibold tracking-widest text-gray-900 uppercase rounded-lg dark:text-white focus:outline-none focus:shadow-outline"
              >
                <img
                  className="w-auto h-24 flex items-start"
                  src={logo}
                  alt=""
                />
              </a>
              <button
                className="rounded-lg md:hidden focus:outline-none focus:shadow-outline"
                onClick={() => setOpen(!open)}
              >
                <svg
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  className="w-6 h-6"
                >
                  {open ? (
                    <path
                      fillRule="evenodd"
                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  ) : (
                    <path
                      fillRule="evenodd"
                      d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM9 15a1 1 0 011-1h6a1 1 0 110 2h-6a1 1 0 01-1-1z"
                      clipRule="evenodd"
                    />
                  )}
                </svg>
              </button>
            </div>

            <nav
              className={`flex-col flex-grow pb-4 md:pb-0 md:flex md:justify-end md:flex-row ${
                open ? "flex" : "hidden"
              }`}
            >
              <a
                className="px-4 py-2 mt-2 text-sm font-semibold hover:text-black rounded-lg md:mt-0 md:ml-4"
                href="#"
              >
                Blog
              </a>
              <a
                className="px-4 py-2 mt-2 text-sm font-semibold hover:text-black rounded-lg md:mt-0 md:ml-4"
                href="#"
              >
                Portfolio
              </a>
              <a
                className="px-4 py-2 mt-2 text-sm font-semibold hover:text-black rounded-lg md:mt-0 md:ml-4"
                href="#"
              >
                About
              </a>
              <a
                className="px-4 py-2 mt-2 text-sm font-semibold hover:text-black rounded-lg md:mt-0 md:ml-4"
                href="#"
              >
                Contact
              </a>

              {/* Dropdown */}
              <div className="relative md:ml-4 mt-2 md:mt-0">
                <button
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  className="flex items-center px-4 py-2 text-sm font-semibold bg-gray-200 rounded-lg hover:text-black"
                  style={{ backgroundColor: "rgb(34, 49, 71)" }}
                >
                  More
                  <svg
                    fill="currentColor"
                    viewBox="0 0 20 20"
                    className={`w-4 h-4 ml-1 transform transition-transform ${
                      dropdownOpen ? "rotate-180" : ""
                    }`}
                  >
                    <path
                      fillRule="evenodd"
                      d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>

                {dropdownOpen && (
                  <div className="absolute right-0 w-64 mt-2 bg-white shadow-lg rounded-md z-50">
                    <div
                      className="p-2 space-y-2"
                      style={{
                        backgroundColor:
                          "rgb(31 41 55 / var(--tw-bg-opacity, 1))",
                      }}
                    >
                      <a
                        href="#"
                        className="block px-4 py-2 hover:text-black rounded"
                      >
                        Appearance
                      </a>
                      <a
                        href="#"
                        className="block px-4 py-2 hover:text-black rounded"
                      >
                        Comments
                      </a>
                      <a
                        href="#"
                        className="block px-4 py-2 hover:text-black rounded"
                      >
                        Analytics
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </nav>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Navbar;

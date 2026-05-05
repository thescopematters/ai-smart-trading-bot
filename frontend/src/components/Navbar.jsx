import React, { useState } from 'react';
import { Menu, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import tsmLogo from '../assets/tsm-logo-new.webp';

const Navbar = () => {
    const [isOpen, setIsOpen] = useState(false);
    const navigate = useNavigate();

    return (
        <nav className="bg-[#072042] text-white shadow-md sticky top-0 z-50">
            <div className="w-full px-4 sm:px-6 lg:px-12">
                <div className="flex justify-between h-16 items-center">
                    <div className="flex-shrink-0 flex items-center">
                        <a
                            href="#"
                            onClick={(e) => {
                                e.preventDefault();
                                navigate('/');
                            }}
                            className="cursor-pointer"
                        >
                            <img src={tsmLogo} alt="TSM - The Scope Matters" className="h-12 w-auto" />
                        </a>
                    </div>

                    <div className="hidden md:flex items-center space-x-8">
                        <a
                            href="#"
                            onClick={(e) => {
                                e.preventDefault();
                                navigate('/');
                            }}
                            className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-semibold transition-all relative group"
                        >
                            Home
                            <span className="absolute bottom-0 left-0 w-full h-0.5 bg-white transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 ease-in-out"></span>
                        </a>
                        <a
                            href="https://thescopematters.com"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-semibold transition-all relative group"
                        >
                            About Us
                            <span className="absolute bottom-0 left-0 w-full h-0.5 bg-white transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 ease-in-out"></span>
                        </a>
                    </div>

                    <div className="md:hidden flex items-center">
                        <button
                            onClick={() => setIsOpen(!isOpen)}
                            className="text-gray-300 hover:text-white focus:outline-none"
                        >
                            {isOpen ? <X size={24} /> : <Menu size={24} />}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile menu */}
            {isOpen && (
                <div className="md:hidden bg-[#072042] border-t border-gray-800">
                    <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
                        <a
                            href="#"
                            onClick={(e) => {
                                e.preventDefault();
                                navigate('/');
                                setIsOpen(false);
                            }}
                            className="text-gray-300 hover:text-white block px-3 py-2 rounded-md text-base font-semibold"
                        >
                            Home
                        </a>
                        <a
                            href="https://thescopematters.com"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-gray-300 hover:text-white block px-3 py-2 rounded-md text-base font-semibold"
                        >
                            About Us
                        </a>
                    </div>
                </div>
            )}
        </nav>
    );
};

export default Navbar;
